"""Exact UTF-8 source identity boundaries for opt-in generation CAS.

The frozen Memory v1 API still uses its own character-based input contract.
Only the opt-in lifetime CAS / manual review requires exact bounded bytes.
No retained token grants consent, replay or external execution permission.
"""

from __future__ import annotations

import pytest

from ark.memory import MemoryScope, MemoryWrite, SQLiteMemoryStore
from ark.memory.generation_cas_outcome_review import (
    MemoryCASOutcomeRejected,
    review_memory_generation_cas_outcome,
)
from ark.memory.generation_fenced_cas import (
    MemoryGenerationCASRejected,
    generation_fenced_memory_update,
    observe_memory_generation_for_cas,
)

_INVALID_SOURCE = (
    "\ud800",
    "\udfff",
    "é" * 257,
    "あ" * 171,
    "x" * 513,
    "\t\n",
)


@pytest.mark.parametrize("source", _INVALID_SOURCE)
def test_observation_rejects_malformed_source_before_readonly_sqlite(
    tmp_path, monkeypatch, source,
):
    store = SQLiteMemoryStore(tmp_path / "invalid-source.sqlite", clock_ms=lambda: 100)

    def forbidden():
        pytest.fail("unbounded source may not reach private SQLite")

    monkeypatch.setattr(store, "_connect_readonly", forbidden)
    with pytest.raises(MemoryGenerationCASRejected):
        observe_memory_generation_for_cas(
            store, MemoryScope("fixture-owner", "private"), source,
        )


@pytest.mark.parametrize("source", _INVALID_SOURCE)
def test_mutated_write_source_cannot_consume_retained_token(
    tmp_path, monkeypatch, source,
):
    path = tmp_path / "generation.sqlite"
    scope = MemoryScope("fixture-owner", "private")
    store = SQLiteMemoryStore(path, clock_ms=lambda: 100)
    original = store.put(MemoryWrite(scope, "fixture-source", "old"))
    token = observe_memory_generation_for_cas(store, scope, "fixture-source")
    proposed = MemoryWrite(scope, "fixture-source", "new")
    object.__setattr__(proposed, "source_id", source)

    def forbidden():
        pytest.fail("invalid source may not open a write transaction")

    monkeypatch.setattr(store, "_connect", forbidden)
    with pytest.raises(MemoryGenerationCASRejected):
        generation_fenced_memory_update(store, proposed, retained=token)

    cold = SQLiteMemoryStore(path, clock_ms=lambda: 100)
    assert cold.get(original.memory_id, scope).content == "old"
    assert len(cold.events(scope)) == 1
    assert observe_memory_generation_for_cas(
        cold, scope, "fixture-source",
    ) == token


@pytest.mark.parametrize("source", _INVALID_SOURCE)
def test_manual_outcome_review_rejects_source_before_private_read(
    tmp_path, monkeypatch, source,
):
    store = SQLiteMemoryStore(tmp_path / "review.sqlite", clock_ms=lambda: 100)
    scope = MemoryScope("fixture-owner", "private")
    store.put(MemoryWrite(scope, "fixture-source", "old"))
    retained = observe_memory_generation_for_cas(store, scope, "fixture-source")
    proposed = MemoryWrite(scope, "fixture-source", "new")
    object.__setattr__(proposed, "source_id", source)

    def forbidden():
        pytest.fail("manual outcome review may not access an invalid identity")

    monkeypatch.setattr(store, "_connect_readonly", forbidden)
    with pytest.raises(MemoryCASOutcomeRejected):
        review_memory_generation_cas_outcome(store, proposed, retained=retained)


@pytest.mark.parametrize(
    "source",
    (
        "x" * 512,
        "é" * 256,
        "あ" * 170 + "ab",
    ),
)
def test_exact_512_utf8_byte_identity_remains_locally_updatable(tmp_path, source):
    path = tmp_path / "valid-boundary.sqlite"
    scope = MemoryScope("fixture-owner", "private")
    first = SQLiteMemoryStore(path, clock_ms=lambda: 100)
    old = first.put(MemoryWrite(scope, source, "before"))
    token = observe_memory_generation_for_cas(first, scope, source)
    other = SQLiteMemoryStore(path, clock_ms=lambda: 100)
    updated = generation_fenced_memory_update(
        other, MemoryWrite(scope, source, "after"), retained=token,
    )
    outcome = review_memory_generation_cas_outcome(
        first, MemoryWrite(scope, source, "after"), retained=token,
    )
    assert updated.memory_id == old.memory_id
    assert updated.revision == 2
    assert outcome.observation == "ONE_MATCHING_UPDATE_OBSERVED"
    assert outcome.commit_attributed_to_caller is False
    assert outcome.automatic_retry_authorized is False
    assert outcome.external_action_authorized is False
    assert len(first.events(scope)) == 2
