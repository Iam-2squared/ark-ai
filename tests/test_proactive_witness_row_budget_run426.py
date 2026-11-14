"""A validated trigger ledger still has a bounded witness hashing phase.

Read-only disposable SQLite fixtures; never deliver notifications, execute
tools or treat history digests as trusted consent/identity.
"""

import sqlite3

import pytest

import ark.proactive_synthetic_continuity_review as continuity
from ark.proactive_synthetic_review import (
    SyntheticProactiveLedger,
    SyntheticTriggerPolicy,
    SyntheticTriggerRejected,
)


def _two_rows(tmp_path):
    ledger = SyntheticProactiveLedger(tmp_path / "proactive.sqlite")
    policy = SyntheticTriggerPolicy(
        "offline-owner", "private", "fixture-trigger", 1, "rev-1",
        1, 100, 10,
    )
    for offset, marker in enumerate(("b", "c")):
        ledger.prepare(
            policy, source_digest="a" * 64,
            observation_digest=marker * 64,
            observed_at_ms=100 + offset, now_ms=100 + offset,
        )
    return ledger


@pytest.mark.parametrize(("budget", "expected_calls"), ((0, 0), (1, 1)))
def test_witness_budget_denies_before_hashing_overflow_row(
    tmp_path, monkeypatch, budget, expected_calls,
):
    ledger = _two_rows(tmp_path)
    real_digest = continuity._digest
    calls = []

    def count_row_hashes(label, data):
        if label == "ARK-trigger-row-v1":
            calls.append(label)
        return real_digest(label, data)

    monkeypatch.setattr(continuity, "_MAX_WITNESS_ROWS", budget)
    monkeypatch.setattr(continuity, "_digest", count_row_hashes)
    with pytest.raises(SyntheticTriggerRejected, match="row scan budget"):
        continuity.read_proactive_witness(ledger)
    assert len(calls) == expected_calls
    with sqlite3.connect(ledger.path) as conn:
        assert conn.execute(
            "SELECT COUNT(*) FROM synthetic_prepared_triggers"
        ).fetchone() == (2,)


def test_independent_retained_witness_not_rebased_to_a_truncated_hash_scan(
    tmp_path, monkeypatch,
):
    ledger = _two_rows(tmp_path)
    retained = continuity.read_proactive_witness(ledger)
    assert len(retained.row_hashes) == 2
    monkeypatch.setattr(continuity, "_MAX_WITNESS_ROWS", 1)
    with pytest.raises(SyntheticTriggerRejected, match="row scan budget"):
        continuity.read_proactive_witness(ledger, retained=retained)
    assert retained.row_hashes == continuity.read_proactive_witness.__globals__[
        "SyntheticTriggerWitness"
    ](retained.row_hashes, retained.digest).row_hashes


def test_exact_witness_hash_budget_accepts_both_rows_with_no_action(
    tmp_path, monkeypatch,
):
    ledger = _two_rows(tmp_path)
    monkeypatch.setattr(continuity, "_MAX_WITNESS_ROWS", 2)
    witness = continuity.read_proactive_witness(ledger)
    assert len(witness.row_hashes) == 2
    assert len(set(witness.row_hashes)) == 2
    witness.assert_integrity()
