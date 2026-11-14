"""Retained privacy revocations cannot validate through replaced methods."""

import pytest

from ark.memory.contracts import MemoryScope
from ark.personal_context_revocation_continuity_review import (
    SyntheticRevocationWitness,
    review_revocation_continuity,
)
from ark.personal_context_revocation_review import (
    SyntheticContextRevocationLedger,
    SyntheticContextRevocationRejected,
)


def test_swapped_noop_validator_cannot_accept_forged_retained_hash(
    tmp_path, monkeypatch,
):
    ledger = SyntheticContextRevocationLedger(tmp_path / "revocations.sqlite")
    ledger.revoke(MemoryScope("owner", "notes"), at_ms=200)
    retained = review_revocation_continuity(ledger)
    object.__setattr__(retained, "witness_id", "rvk_" + "0" * 64)
    monkeypatch.setattr(
        SyntheticRevocationWitness, "assert_integrity", lambda self: None,
    )
    with pytest.raises(
        SyntheticContextRevocationRejected, match="validator changed",
    ):
        review_revocation_continuity(ledger, retained=retained)


def test_preinstalled_noop_validator_cannot_normalize_any_retained_tip(
    tmp_path, monkeypatch,
):
    ledger = SyntheticContextRevocationLedger(tmp_path / "empty.sqlite")
    retained = review_revocation_continuity(ledger)
    monkeypatch.setattr(
        SyntheticRevocationWitness, "assert_integrity", lambda self: None,
    )
    with pytest.raises(
        SyntheticContextRevocationRejected, match="validator changed",
    ):
        review_revocation_continuity(ledger, retained=retained)


def test_unmodified_validator_preserves_append_only_diagnostic(tmp_path):
    ledger = SyntheticContextRevocationLedger(tmp_path / "normal.sqlite")
    previous = review_revocation_continuity(ledger)
    ledger.revoke(MemoryScope("owner", "notes"), at_ms=100)
    current = review_revocation_continuity(ledger, retained=previous)
    assert current.witness_id != previous.witness_id
    assert len(current.rows) == 1
