"""Post-COMMIT manual-only review rejects reflected bad inputs before SQLite.

The fixture never retries the write or attributes another writer's commit.
"""
from __future__ import annotations

import pytest

from ark.memory import MemoryScope, MemoryWrite, SQLiteMemoryStore
from ark.memory import generation_cas_outcome_review as outcome
from ark.memory.generation_cas_outcome_review import (
    MemoryCASOutcomeRejected,
    review_memory_generation_cas_outcome,
)
from ark.memory.generation_fenced_cas import observe_memory_generation_for_cas


def _prepared(tmp_path):
    store = SQLiteMemoryStore(
        tmp_path / "outcome-preaccess.sqlite", clock_ms=lambda: 1_000,
    )
    scope = MemoryScope("local-fixture", "private")
    saved = store.put(MemoryWrite(scope, "stable", "prior"))
    retained = observe_memory_generation_for_cas(store, scope, "stable")
    proposed = MemoryWrite(scope, "stable", "next")
    return store, scope, saved, retained, proposed


@pytest.mark.parametrize(
    ("field", "replacement", "diagnostic"),
    (
        ("source_id", "あ" * 171, "bounded valid UTF-8 source"),
        ("source_id", "broken\ud800", "bounded valid UTF-8 source"),
        ("source_id", " ", "bounded valid UTF-8 source"),
        ("content", "broken\udfff", "valid UTF-8 content"),
        ("content", b"not-text", "exact bounded content"),
        ("content", "x" * 1_000_001, "exact bounded content"),
    ),
)
def test_bad_reflected_proposal_never_hashes_or_opens_memory(
    monkeypatch, tmp_path, field, replacement, diagnostic,
):
    store, scope, saved, retained, proposed = _prepared(tmp_path)
    event_image = tuple(store.events(scope))
    object.__setattr__(proposed, field, replacement)

    def forbidden(*_args, **_kwargs):
        pytest.fail("malformed CAS proposal reached SQLite or payload hashing")

    # Restore the read hook before checking the untouched event history.
    # Only the review under test is forbidden from opening SQLite.
    with monkeypatch.context() as isolated:
        isolated.setattr(store, "_connect_readonly", forbidden)
        with pytest.raises(MemoryCASOutcomeRejected, match=diagnostic):
            review_memory_generation_cas_outcome(
                store, proposed, retained=retained,
            )
    assert tuple(store.events(scope)) == event_image
    assert store.get(saved.memory_id, scope, include_expired=True) == saved


def test_valid_manual_only_proposal_unchanged_and_has_no_retry_authority(tmp_path):
    store, scope, saved, retained, proposed = _prepared(tmp_path)
    before = tuple(store.events(scope))
    outcome = review_memory_generation_cas_outcome(
        store, proposed, retained=retained,
    )
    assert outcome.observation == "UNCHANGED_OBSERVED"
    assert outcome.commit_attributed_to_caller is False
    assert outcome.automatic_retry_authorized is False
    assert outcome.consent_authenticated is False
    assert outcome.external_action_authorized is False
    assert tuple(store.events(scope)) == before
    assert store.get(saved.memory_id, scope, include_expired=True) == saved


@pytest.mark.parametrize(
    "changed",
    ("hashlib_module", "json_module", "sha256", "dumps",
     "domain", "equal_domain_replacement"),
)
def test_outcome_digest_preflight_blocks_injected_code_before_private_read(
    monkeypatch, tmp_path, changed,
):
    store, scope, saved, retained, proposed = _prepared(tmp_path)
    untouched = tuple(store.events(scope))
    invoked = []

    def forbidden(*args, **kwargs):
        invoked.append((args, kwargs))
        raise AssertionError("untrusted digest or private SQLite access")

    with monkeypatch.context() as patch:
        patch.setattr(store, "_connect_readonly", forbidden)
        if changed == "hashlib_module":
            patch.setattr(outcome, "hashlib", object())
        elif changed == "json_module":
            patch.setattr(outcome, "json", object())
        elif changed == "sha256":
            patch.setattr(outcome.hashlib, "sha256", forbidden)
        elif changed == "dumps":
            patch.setattr(outcome.json, "dumps", forbidden)
        elif changed == "domain":
            patch.setattr(outcome, "_DOMAIN", b"wrong-outcome-domain")
        else:
            replacement = bytes(bytearray(outcome._DOMAIN))
            assert replacement == outcome._DOMAIN
            assert replacement is not outcome._DOMAIN
            patch.setattr(outcome, "_DOMAIN", replacement)
        with pytest.raises(
            MemoryCASOutcomeRejected, match="digest implementation changed",
        ):
            outcome.review_memory_generation_cas_outcome(
                store, proposed, retained=retained,
            )
    assert invoked == []
    reviewed = outcome.review_memory_generation_cas_outcome(
        store, proposed, retained=retained,
    )
    assert reviewed.observation == "UNCHANGED_OBSERVED"
    assert reviewed.automatic_retry_authorized is False
    assert reviewed.consent_authenticated is False
    assert tuple(store.events(scope)) == untouched
    assert store.get(saved.memory_id, scope, include_expired=True) == saved
