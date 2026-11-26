"""Retained due-slot CAS must use storage scalars, not forgeable equality.

These are synthetic local reservations. They are not trusted time, consent,
notification or ToolBackend dispatch authorization.
"""

from __future__ import annotations

import pytest

from ark.agency import disconnected_due_reservation as due


def _one_saved(tmp_path):
    path = tmp_path / "due-scalar.sqlite"
    ledger = due.DisconnectedDueReservations(path)
    first = ledger.reserve_due(
        policy_sha256="a" * 64,
        due_at_ms=10,
        observed_now_ms=11,
        retained=due.genesis_due_witness(),
    )
    return path, ledger, first.witness


@pytest.mark.parametrize("stale_kind", ["old_count", "wrong_tip"])
def test_stale_reservation_rejected_even_with_forged_always_true_equality(
    tmp_path, monkeypatch, stale_kind,
):
    _, ledger, latest = _one_saved(tmp_path)
    retained = (
        due.genesis_due_witness()
        if stale_kind == "old_count"
        else due.DueReservationWitness(latest.count, "f" * 64)
    )
    monkeypatch.setattr(due.DueReservationWitness, "__eq__", lambda _a, _b: True)
    with pytest.raises(due.DueReservationRejected, match="stale or rewritten"):
        ledger.reserve_due(
            policy_sha256="b" * 64,
            due_at_ms=12,
            observed_now_ms=13,
            retained=retained,
        )
    observed = ledger.witness()
    assert observed.count == latest.count
    assert observed.fingerprint == latest.fingerprint


@pytest.mark.parametrize("stale_kind", ["old_count", "wrong_tip"])
def test_restart_rejects_stale_witness_even_with_forged_equality(
    tmp_path, monkeypatch, stale_kind,
):
    path, _, latest = _one_saved(tmp_path)
    retained = (
        due.genesis_due_witness()
        if stale_kind == "old_count"
        else due.DueReservationWitness(latest.count, "f" * 64)
    )
    monkeypatch.setattr(due.DueReservationWitness, "__eq__", lambda _a, _b: True)
    with pytest.raises(due.DueReservationRejected, match="differs on restart"):
        due.DisconnectedDueReservations.reopen_with_witness(
            path, retained=retained,
        )


def test_matching_retained_reservation_survives_forged_always_false_equality(
    tmp_path, monkeypatch,
):
    _, ledger, latest = _one_saved(tmp_path)
    monkeypatch.setattr(due.DueReservationWitness, "__eq__", lambda _a, _b: False)
    receipt = ledger.reserve_due(
        policy_sha256="b" * 64,
        due_at_ms=12,
        observed_now_ms=13,
        retained=latest,
    )
    assert receipt.witness.count == 2
    assert receipt.execution_authorized is False
    assert receipt.notification_authorized is False
    assert receipt.automatic_replay_authorized is False
    assert receipt.trusted_clock_verified is False


def test_matching_retained_restart_survives_forged_always_false_equality(
    tmp_path, monkeypatch,
):
    path, _, latest = _one_saved(tmp_path)
    monkeypatch.setattr(due.DueReservationWitness, "__eq__", lambda _a, _b: False)
    restarted = due.DisconnectedDueReservations.reopen_with_witness(
        path, retained=latest,
    )
    observed = restarted.witness()
    assert observed.count == latest.count
    assert observed.fingerprint == latest.fingerprint
    assert observed.independent_custody_proven is False
