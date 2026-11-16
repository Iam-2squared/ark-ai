"""Persistent disconnected due-reservation source pinning.

No trusted clock, consent, notifications, replay, or tool execution.
"""

from __future__ import annotations

from pathlib import Path

import pytest

import ark.agency.disconnected_due_reservation as due
from ark.agency.disconnected_due_reservation import (
    DisconnectedDueReservations,
    DueReservationRejected,
)


@pytest.mark.parametrize("replacement", ("different", "equal-new-path"))
@pytest.mark.parametrize("operation", ("witness", "reserve"))
def test_initialized_ledger_never_follows_rebound_source(
    tmp_path, monkeypatch, replacement, operation,
):
    original = DisconnectedDueReservations(tmp_path / "original.sqlite")
    another = DisconnectedDueReservations(tmp_path / "other.sqlite")
    retained = original.witness()
    if replacement == "different":
        original._path = another._path
    else:
        original._path = Path(str(original._path))
        assert original._path == original._source_path_epoch
        assert original._path is not original._source_path_epoch

    # Ordinary path metadata validation must not inspect a substituted
    # carrier, including a value-equal replacement and a valid other ledger.
    def forbidden_path(_path, *, exists):
        raise AssertionError("substituted path reached metadata")

    monkeypatch.setattr(due, "_check_path", forbidden_path)
    with pytest.raises(DueReservationRejected, match="source identity changed"):
        if operation == "witness":
            original.witness()
        else:
            original.reserve_due(
                policy_sha256="a" * 64, due_at_ms=10,
                observed_now_ms=11, retained=retained,
            )
    assert another._path.is_file()


def test_untouched_ledger_receipt_and_readonly_restart(tmp_path):
    path = tmp_path / "due.sqlite"
    original = DisconnectedDueReservations(path)
    before = original.witness()
    receipt = original.reserve_due(
        policy_sha256="b" * 64, due_at_ms=100,
        observed_now_ms=101, retained=before,
    )
    assert receipt.witness.count == before.count + 1
    assert receipt.witness.independent_custody_proven is False
    assert receipt.execution_authorized is False
    assert receipt.notification_authorized is False
    assert receipt.automatic_replay_authorized is False
    assert receipt.trusted_clock_verified is False
    reopened = DisconnectedDueReservations.reopen_with_witness(
        path, retained=receipt.witness,
    )
    assert reopened.witness() == receipt.witness
