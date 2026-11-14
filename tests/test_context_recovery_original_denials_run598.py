"""Personal Context restart diagnostics reject reinstalled False-only authority.

All fixtures use ephemeral SQLite and hash-only identifiers. Neither receipt
nor retained witness authorizes use, retention, disclosure, or execution.
"""

import pytest

import ark.personal_context_replay_recovery as recovery
from ark.personal_context_replay_ledger import (
    DisconnectedContextReplayLedger,
    OfflineContextReplayWitness,
)


def _fixture(tmp_path):
    ledger = DisconnectedContextReplayLedger(
        tmp_path / "synthetic-context-recovery.sqlite", create=True,
    )
    return ledger, ledger.witness()


@pytest.mark.parametrize("flag", (
    "historical_prefix_proven", "independent_custody_proven",
    "consent_verified", "revocation_freshness_verified",
    "context_disclosure_authorized", "tool_dispatch_authorized",
    "automatic_replay_authorized",
))
def test_preinstalled_false_only_result_descriptor_never_called(
    tmp_path, monkeypatch, flag,
):
    ledger, witness = _fixture(tmp_path)
    hits = []

    def fake_getter(_self):
        hits.append(flag)
        return False

    monkeypatch.setattr(
        recovery.OfflineContextRecoveryReview, flag, property(fake_getter),
    )
    with pytest.raises(
        recovery.OfflineContextRecoveryRejected,
        match="context replay review result gained authority",
    ):
        recovery.review_restarted_context_replay(ledger, witness)
    assert hits == []
    assert ledger.witness() == witness


def test_preinstalled_false_only_retained_witness_getter_never_called(
    tmp_path, monkeypatch,
):
    ledger, witness = _fixture(tmp_path)
    hits = []

    def fake_getter(_self):
        hits.append("forged")
        return False

    monkeypatch.setattr(
        OfflineContextReplayWitness, "independent_custody_proven",
        property(fake_getter),
    )
    with pytest.raises(
        recovery.OfflineContextRecoveryRejected,
        match="invalid exact context replay witness",
    ):
        recovery.review_restarted_context_replay(ledger, witness)
    assert hits == []


def test_late_false_descriptor_replacement_is_rejected_without_invocation(
    tmp_path, monkeypatch,
):
    ledger, witness = _fixture(tmp_path)
    original_inspect = recovery._inspect
    calls = []
    hits = []

    def fake_getter(_self):
        hits.append("late")
        return False

    def swap_after_first_report(conn):
        observed = original_inspect(conn)
        calls.append(1)
        if len(calls) == 2:
            monkeypatch.setattr(
                recovery.OfflineContextRecoveryReview,
                "automatic_replay_authorized", property(fake_getter),
            )
        return observed

    monkeypatch.setattr(recovery, "_inspect", swap_after_first_report)
    with pytest.raises(
        recovery.OfflineContextRecoveryRejected,
        match="context replay review result gained authority",
    ):
        recovery.review_restarted_context_replay(ledger, witness)
    assert len(calls) >= 2
    assert hits == []


def test_unmodified_context_recovery_remains_non_authorizing(tmp_path):
    ledger, witness = _fixture(tmp_path)
    result = recovery.review_restarted_context_replay(ledger, witness)
    assert result.status == "UNCHANGED_LOCAL_HISTORY"
    assert result.consent_verified is False
    assert result.automatic_replay_authorized is False
