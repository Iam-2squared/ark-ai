"""Synthetic privacy review must never acquire deletion, export, or use authority."""

from __future__ import annotations

import pytest

import ark.personal_context_retention_recheck_review as review
from ark.memory.contracts import MemoryScope, MemoryWrite
from ark.memory.sqlite_store import SQLiteMemoryStore
from ark.personal_context_retention_review import review_synthetic_retention_inventory
from ark.personal_context_revocation_review import SyntheticContextRevocationLedger


def setup(tmp_path):
    memory = SQLiteMemoryStore(tmp_path / "memory.sqlite", clock_ms=lambda: 100)
    scope = MemoryScope("offline-owner", "private")
    memory.put(MemoryWrite(
        scope, "fixture-1", "SENSITIVE CONTENT NEVER IN RESULT",
        expires_at_ms=101,
    ))
    revocations = SyntheticContextRevocationLedger(tmp_path / "veto.sqlite")
    cached = review_synthetic_retention_inventory(
        memory, scope, revocations, now_ms=100,
    )
    return memory, scope, revocations, cached


def test_unchanged_diagnostic_remains_non_authorizing(tmp_path):
    outcome = review.review_synthetic_retention_recheck(
        *setup(tmp_path), now_ms=101, max_age_ms=10,
    )
    assert outcome.deletion_authorized is False
    assert outcome.erasure_completed is False
    assert outcome.context_use_authorized is False
    assert outcome.external_disclosure_authorized is False
    assert "SENSITIVE CONTENT" not in repr(outcome)


@pytest.mark.parametrize("flag", (
    "deletion_authorized",
    "erasure_completed",
    "context_use_authorized",
    "external_disclosure_authorized",
))
def test_authority_property_rebinding_is_rejected(tmp_path, monkeypatch, flag):
    state = setup(tmp_path)
    monkeypatch.setattr(
        review.SyntheticRetentionRecheck,
        flag,
        property(lambda _self: True),
    )
    with pytest.raises(
        review.SyntheticRetentionRecheckRejected,
        match="returned result changed",
    ):
        review.review_synthetic_retention_recheck(
            *state, now_ms=101, max_age_ms=10,
        )


def test_module_constructor_rebinding_cannot_forge_compatible_report(
    tmp_path, monkeypatch,
):
    state = setup(tmp_path)
    native = review.SyntheticRetentionRecheck

    class Forged(native):
        pass

    monkeypatch.setattr(review, "SyntheticRetentionRecheck", Forged)
    with pytest.raises(
        review.SyntheticRetentionRecheckRejected,
        match="returned result changed",
    ):
        review.review_synthetic_retention_recheck(
            *state, now_ms=101, max_age_ms=10,
        )
