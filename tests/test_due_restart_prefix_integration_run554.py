"""Restart recovery refuses an append which rewrites its retained due prefix."""

import sqlite3
from dataclasses import replace

import pytest

import ark.agency.disconnected_due_recovery_review as recovery
from ark.agency.disconnected_due_reservation import (
    DisconnectedDueReservations,
    genesis_due_witness,
)


def _ledger(tmp_path):
    ledger = DisconnectedDueReservations(tmp_path / "due-restart.sqlite3")
    first = ledger.reserve_due(
        policy_sha256="a" * 64,
        due_at_ms=1000,
        observed_now_ms=1005,
        retained=genesis_due_witness(),
    )
    return ledger, first.witness


def _append(ledger, retained):
    return ledger.reserve_due(
        policy_sha256="b" * 64,
        due_at_ms=2000,
        observed_now_ms=2010,
        retained=retained,
    ).witness


def test_append_preserves_prefix_but_does_not_authenticate_a_writer(tmp_path):
    ledger, retained = _ledger(tmp_path)
    _append(ledger, retained)
    result = recovery.review_restarted_due_reservations(ledger, retained)
    assert (result.previous_count, result.observed_count) == (1, 2)
    assert result.status == "ADVANCED_HISTORY_UNVERIFIED"
    assert result.historical_prefix_proven is False
    assert result.independently_custodied is False
    assert result.notification_authorized is False
    assert result.tool_dispatch_authorized is False
    assert result.automatic_replay_authorized is False


@pytest.mark.parametrize("changed_timestamp", (1006, 1007))
def test_valid_new_head_cannot_hide_rewritten_retained_prefix(
    tmp_path, changed_timestamp,
):
    ledger, retained = _ledger(tmp_path)
    _append(ledger, retained)
    # The forged row still has a valid time, policy-bound slot ID and order.
    # Only a separately retained prefix detects the silent historical edit.
    with sqlite3.connect(ledger._path) as conn:
        conn.execute(
            "UPDATE due_reservations SET reserved_at_ms=? WHERE seq=1",
            (changed_timestamp,),
        )
    assert ledger.witness().count == 2
    with pytest.raises(
        recovery.DisconnectedDueRecoveryRejected, match="prefix rejected"
    ):
        recovery.review_restarted_due_reservations(ledger, retained)


def test_append_between_snapshot_reads_is_not_a_coherent_restart(tmp_path, monkeypatch):
    ledger, retained = _ledger(tmp_path)
    original = recovery.review_retained_due_prefix

    def concurrent_append(store, old):
        _append(store, store.witness())
        return original(store, old)

    monkeypatch.setattr(recovery, "review_retained_due_prefix", concurrent_append)
    with pytest.raises(
        recovery.DisconnectedDueRecoveryRejected, match="observation drifted"
    ):
        recovery.review_restarted_due_reservations(ledger, retained)


def test_forged_prefix_result_cannot_change_observed_count(tmp_path, monkeypatch):
    ledger, retained = _ledger(tmp_path)
    _append(ledger, retained)
    original = recovery.review_retained_due_prefix

    def fabricated(*args):
        result = original(*args)
        return replace(result, current_count=result.current_count + 1)

    monkeypatch.setattr(recovery, "review_retained_due_prefix", fabricated)
    with pytest.raises(
        recovery.DisconnectedDueRecoveryRejected, match="observation drifted"
    ):
        recovery.review_restarted_due_reservations(ledger, retained)


def test_prefix_authority_substitution_fails_closed(tmp_path, monkeypatch):
    ledger, retained = _ledger(tmp_path)
    monkeypatch.setattr(
        recovery.DisconnectedDuePrefixReview,
        "notification_authorized",
        property(lambda self: True),
    )
    with pytest.raises(
        recovery.DisconnectedDueRecoveryRejected, match="prefix rejected"
    ):
        recovery.review_restarted_due_reservations(ledger, retained)
