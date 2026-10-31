"""Due-slot restart/reads cannot confer authority through altered witnesses."""

from __future__ import annotations

import pytest

from ark.agency import disconnected_due_reservation as due


class ForgedWitness(due.DueReservationWitness):
    @property
    def independent_custody_proven(self) -> bool:
        return True


def _forged() -> ForgedWitness:
    genesis = due.genesis_due_witness()
    return ForgedWitness(genesis.count, genesis.fingerprint)


def test_restart_rejects_forged_due_witness_class(tmp_path, monkeypatch):
    path = tmp_path / "due.sqlite"
    due.DisconnectedDueReservations(path)
    monkeypatch.setattr(due, "_inspect", lambda conn: (_forged(), None))
    with pytest.raises(due.DueReservationRejected, match="independently retained"):
        due.DisconnectedDueReservations(path, require_existing=True)


def test_readonly_due_snapshot_rejects_forged_witness(tmp_path, monkeypatch):
    path = tmp_path / "due.sqlite"
    ledger = due.DisconnectedDueReservations(path)
    monkeypatch.setattr(due, "_inspect", lambda conn: (_forged(), None))
    with pytest.raises(due.DueReservationRejected, match="independently retained"):
        ledger.witness()


def test_retained_restart_rejects_authority_changed_between_reads(
    tmp_path, monkeypatch,
):
    path = tmp_path / "due.sqlite"
    due.DisconnectedDueReservations(path)
    retained = due.genesis_due_witness()
    original = due._inspect
    old_property = due.DueReservationWitness.independent_custody_proven
    count = 0

    def forge_second_read(conn):
        nonlocal count
        result = original(conn)
        count += 1
        if count == 2:
            monkeypatch.setattr(
                due.DueReservationWitness,
                "independent_custody_proven",
                property(lambda self: True),
            )
        return result

    monkeypatch.setattr(due, "_inspect", forge_second_read)
    with pytest.raises(due.DueReservationRejected, match="independently retained"):
        due.DisconnectedDueReservations.reopen_with_witness(
            path, retained=retained,
        )
    monkeypatch.setattr(due, "_inspect", original)
    monkeypatch.setattr(
        due.DueReservationWitness, "independent_custody_proven", old_property,
    )
    assert due.DisconnectedDueReservations.reopen_with_witness(
        path, retained=retained,
    ).witness() == retained
