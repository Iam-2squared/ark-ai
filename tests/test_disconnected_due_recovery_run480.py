"""Synthetic due-ledger restart: no execution, consent or history authority."""

from __future__ import annotations

import pytest

import ark.agency.disconnected_due_recovery_review as recovery
from ark.agency.disconnected_due_reservation import (
    DisconnectedDueReservations,
    DueReservationWitness,
)


def _ledger(tmp_path, name="due.sqlite3"):
    return DisconnectedDueReservations(tmp_path / name)


def _reserve(ledger, witness, *, due=100, policy="a"):
    return ledger.reserve_due(
        policy_sha256=policy * 64, due_at_ms=due,
        observed_now_ms=due + 1, retained=witness,
    )


def test_clean_restart_same_witness_has_no_action_authority(tmp_path):
    ledger = _ledger(tmp_path)
    retained = ledger.witness()
    first = _reserve(ledger, retained)
    restarted = _ledger(tmp_path)
    result = recovery.review_restarted_due_reservations(
        restarted, first.witness,
    )
    assert result.status == "UNCHANGED_LOCAL_HISTORY"
    assert result.previous_count == 1
    assert result.observed_count == 1
    assert len(result.digest) == 64
    assert result.historical_prefix_proven is False
    assert result.independently_custodied is False
    assert result.trusted_clock_verified is False
    assert result.notification_authorized is False
    assert result.tool_dispatch_authorized is False
    assert result.automatic_replay_authorized is False


def test_additional_reservation_is_explicitly_unverified(tmp_path):
    ledger = _ledger(tmp_path)
    genesis = ledger.witness()
    first = _reserve(ledger, genesis)
    _reserve(ledger, first.witness, due=120, policy="b")
    restarted = _ledger(tmp_path)
    result = recovery.review_restarted_due_reservations(
        restarted, first.witness,
    )
    assert result.observed_count == 2
    assert result.status == "ADVANCED_HISTORY_UNVERIFIED"
    assert result.historical_prefix_proven is False


def test_synthetic_full_ledger_rollback_is_denied(tmp_path):
    original = _ledger(tmp_path, "earlier.sqlite3")
    first = _reserve(original, original.witness())
    empty = _ledger(tmp_path, "replacement.sqlite3")
    with pytest.raises(
        recovery.DisconnectedDueRecoveryRejected, match="count regressed",
    ):
        recovery.review_restarted_due_reservations(empty, first.witness)


def test_same_count_rewrite_is_denied(tmp_path):
    ledger = _ledger(tmp_path)
    first = _reserve(ledger, ledger.witness())
    changed = DueReservationWitness(1, "f" * 64)
    assert changed.fingerprint != first.witness.fingerprint
    with pytest.raises(
        recovery.DisconnectedDueRecoveryRejected, match="history rewritten",
    ):
        recovery.review_restarted_due_reservations(ledger, changed)


@pytest.mark.parametrize("count", [True, 0.0, -1, 513])
def test_non_exact_or_out_of_budget_count_is_denied(tmp_path, count):
    ledger = _ledger(tmp_path)
    fake = DueReservationWitness(count, ledger.witness().fingerprint)
    with pytest.raises(
        recovery.DisconnectedDueRecoveryRejected, match="invalid exact",
    ):
        recovery.review_restarted_due_reservations(ledger, fake)


def test_retained_witness_modified_during_read_is_denied(tmp_path, monkeypatch):
    ledger = _ledger(tmp_path)
    retained = ledger.witness()
    original = ledger.witness

    def swap():
        current = original()
        object.__setattr__(retained, "fingerprint", "f" * 64)
        return current

    monkeypatch.setattr(ledger, "witness", swap)
    with pytest.raises(
        recovery.DisconnectedDueRecoveryRejected, match="custody changed",
    ):
        recovery.review_restarted_due_reservations(ledger, retained)


def test_constructed_recovery_result_cannot_grant_dispatch(tmp_path, monkeypatch):
    ledger = _ledger(tmp_path)
    retained = ledger.witness()
    monkeypatch.setattr(
        recovery, "DisconnectedDueRecoveryReview", lambda *args: object(),
    )
    with pytest.raises(
        recovery.DisconnectedDueRecoveryRejected, match="result changed",
    ):
        recovery.review_restarted_due_reservations(ledger, retained)


def test_result_is_repeatable_without_appending(tmp_path):
    ledger = _ledger(tmp_path)
    retained = ledger.witness()
    before = recovery.review_restarted_due_reservations(ledger, retained)
    after = recovery.review_restarted_due_reservations(ledger, retained)
    assert before == after
    assert ledger.witness() == retained
