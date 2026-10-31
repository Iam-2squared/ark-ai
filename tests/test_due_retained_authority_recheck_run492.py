"""Retained due-slot identity cannot acquire authority during SQLite inspection.

Only disconnected local reservations are exercised; no real execution or time proof.
"""

from __future__ import annotations

import pytest

from ark.agency import disconnected_due_reservation as due


def _spoof_after_check(monkeypatch, retained, *, number):
    original = due._check_witness
    checks = 0

    def checked(witness):
        nonlocal checks
        original(witness)
        checks += 1
        if checks == number:
            # Spoof only the caller's retained object, not the witnesses
            # reconstructed during SQLite inspection.
            monkeypatch.setattr(
                due.DueReservationWitness,
                "independent_custody_proven",
                property(lambda self: self is retained),
            )

    monkeypatch.setattr(due, "_check_witness", checked)


def test_reopen_rechecks_retained_authority_after_sqlite_snapshot(
    tmp_path, monkeypatch,
):
    path = tmp_path / "due.sqlite"
    due.DisconnectedDueReservations(path)
    retained = due.genesis_due_witness()

    with monkeypatch.context() as patch:
        _spoof_after_check(patch, retained, number=3)
        with pytest.raises(
            due.DueReservationRejected, match="independently retained",
        ):
            due.DisconnectedDueReservations.reopen_with_witness(
                path, retained=retained,
            )

    assert due.DisconnectedDueReservations.reopen_with_witness(
        path, retained=retained,
    ).witness() == retained


def test_reserve_rechecks_retained_authority_before_sqlite_insert(
    tmp_path, monkeypatch,
):
    path = tmp_path / "due.sqlite"
    ledger = due.DisconnectedDueReservations(path)
    retained = due.genesis_due_witness()

    with monkeypatch.context() as patch:
        _spoof_after_check(patch, retained, number=2)
        with pytest.raises(
            due.DueReservationRejected, match="independently retained",
        ):
            ledger.reserve_due(
                policy_sha256="a" * 64, due_at_ms=100,
                observed_now_ms=100, retained=retained,
            )

    assert ledger.witness() == retained
