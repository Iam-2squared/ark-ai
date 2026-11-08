"""Disconnected due restart rejects forged denial callbacks and late witnesses.

This is a read-only synthetic scheduler diagnostic. No clock, notification,
ToolBackend effect, consent or replay is authenticated by these fixtures.
"""

from __future__ import annotations

import pytest

import ark.agency.disconnected_due_recovery_review as recovery
from ark.agency.disconnected_due_reservation import (
    DisconnectedDueReservations,
    DueReservationRejected,
)


def _ledger(tmp_path):
    ledger = DisconnectedDueReservations(tmp_path / "due-restart.sqlite3")
    return ledger, ledger.witness()


@pytest.mark.parametrize("flag", recovery._RESULT_DENIALS)
def test_preinstalled_false_restart_result_denial_is_rejected(
    tmp_path, monkeypatch, flag,
):
    ledger, retained = _ledger(tmp_path)
    entered = []

    def false_callback(self):
        entered.append(flag)
        return False

    with monkeypatch.context() as patch:
        patch.setattr(recovery.DisconnectedDueRecoveryReview, flag,
                      property(false_callback))
        with pytest.raises(
            recovery.DisconnectedDueRecoveryRejected, match="result changed",
        ):
            recovery.review_restarted_due_reservations(ledger, retained)
    assert entered == []


@pytest.mark.parametrize("flag", recovery._PREFIX_DENIALS)
def test_preinstalled_false_prefix_denial_cannot_certify_restart(
    tmp_path, monkeypatch, flag,
):
    ledger, retained = _ledger(tmp_path)
    entered = []

    def false_callback(self):
        entered.append(flag)
        return False

    with monkeypatch.context() as patch:
        patch.setattr(recovery.DisconnectedDuePrefixReview, flag,
                      property(false_callback))
        with pytest.raises(recovery.DisconnectedDueRecoveryRejected):
            recovery.review_restarted_due_reservations(ledger, retained)


def test_preinstalled_false_witness_denial_rejected_before_read(
    tmp_path, monkeypatch,
):
    ledger, retained = _ledger(tmp_path)
    entered = []

    def false_callback(self):
        entered.append(True)
        return False

    with monkeypatch.context() as patch:
        patch.setattr(recovery._WITNESS_TYPE, "independent_custody_proven",
                      property(false_callback))
        with pytest.raises(
            recovery.DisconnectedDueRecoveryRejected,
            match="(?:invalid exact due|due witness carrier changed)",
        ):
            recovery.review_restarted_due_reservations(ledger, retained)
    assert entered == []


def test_late_rewritten_prefix_report_cannot_escape_restart_review(
    tmp_path, monkeypatch,
):
    ledger, retained = _ledger(tmp_path)
    native = recovery.review_retained_due_prefix
    original_hash = recovery.hashlib.sha256
    captured = []

    def collect(*args):
        result = native(*args)
        captured.append(result)
        return result

    def mutate_at_final_digest(payload):
        if captured:
            object.__setattr__(captured[0], "status", "ALTERED_LOCAL_HISTORY")
        return original_hash(payload)

    with monkeypatch.context() as patch:
        patch.setattr(recovery, "review_retained_due_prefix", collect)
        patch.setattr(recovery.hashlib, "sha256", mutate_at_final_digest)
        # The due ledger now rejects a replaced digest before any prefix
        # review or untrusted hash callback is reached.
        with pytest.raises(
            DueReservationRejected, match="due digest callback authority changed",
        ):
            recovery.review_restarted_due_reservations(ledger, retained)
    assert captured == []
    assert ledger.witness() == retained


def test_clean_due_restart_remains_read_only(tmp_path):
    ledger, retained = _ledger(tmp_path)
    report = recovery.review_restarted_due_reservations(ledger, retained)
    assert report.status == "UNCHANGED_LOCAL_HISTORY"
    assert report.previous_count == report.observed_count == 0
    assert all(getattr(report, flag) is False
               for flag in recovery._RESULT_DENIALS)
    assert ledger.witness() == retained
