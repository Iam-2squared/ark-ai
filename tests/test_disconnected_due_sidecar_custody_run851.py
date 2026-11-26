"""Disconnected due scheduler refuses unsafe SQLite sidecar names.

Only disposable synthetic fixtures, not reminders or actual notifications.
"""

from __future__ import annotations

import os

import pytest

from ark.agency.disconnected_due_reservation import (
    DisconnectedDueReservations,
    DueReservationRejected,
)


@pytest.mark.parametrize("suffix", ("-wal", "-shm", "-journal"))
def test_existing_due_ledger_rejects_directory_sidecar(tmp_path, suffix):
    path = tmp_path / "due.sqlite3"
    ledger = DisconnectedDueReservations(path)
    initial = ledger.witness()
    sidecar = path.with_name(path.name + suffix)
    sidecar.mkdir()
    with pytest.raises(DueReservationRejected, match="sidecar"):
        DisconnectedDueReservations(path, require_existing=True)
    with pytest.raises(DueReservationRejected, match="sidecar"):
        ledger.witness()
    with pytest.raises(DueReservationRejected, match="sidecar"):
        ledger.reserve_due(
            policy_sha256="a" * 64, due_at_ms=10,
            observed_now_ms=11, retained=initial,
        )
    sidecar.rmdir()
    assert ledger.witness() == initial


@pytest.mark.parametrize("suffix", ("-wal", "-shm", "-journal"))
def test_orphaned_due_sidecar_rejected_without_bootstrap(tmp_path, suffix):
    path = tmp_path / "not-created.sqlite3"
    sidecar = path.with_name(path.name + suffix)
    sidecar.write_bytes(b"synthetic")
    with pytest.raises(DueReservationRejected, match="sidecar"):
        DisconnectedDueReservations(path)
    assert not path.exists()
    assert sidecar.read_bytes() == b"synthetic"


@pytest.mark.parametrize("suffix", ("-wal", "-shm", "-journal"))
def test_due_ledger_rejects_hardlinked_sidecar(tmp_path, suffix):
    path = tmp_path / "due.sqlite3"
    DisconnectedDueReservations(path)
    original = tmp_path / "unrelated.bin"
    original.write_bytes(b"keep-unchanged")
    sidecar = path.with_name(path.name + suffix)
    try:
        os.link(original, sidecar)
    except OSError:
        pytest.skip("hardlinks unavailable on this filesystem")
    with pytest.raises(DueReservationRejected, match="sidecar"):
        DisconnectedDueReservations(path, require_existing=True)
    assert original.read_bytes() == b"keep-unchanged"


@pytest.mark.parametrize("suffix", ("-wal", "-shm", "-journal"))
def test_due_ledger_rejects_symlinked_sidecar(tmp_path, suffix):
    path = tmp_path / "due.sqlite3"
    DisconnectedDueReservations(path)
    original = tmp_path / "unrelated.bin"
    original.write_bytes(b"keep-unchanged")
    sidecar = path.with_name(path.name + suffix)
    try:
        sidecar.symlink_to(original)
    except (OSError, NotImplementedError):
        pytest.skip("symlinks unavailable on this filesystem")
    with pytest.raises(DueReservationRejected, match="sidecar"):
        DisconnectedDueReservations(path, require_existing=True)
    assert original.read_bytes() == b"keep-unchanged"


def test_too_long_due_path_rejected_before_creating_any_file(tmp_path):
    path = tmp_path / ("x" * 4100)
    with pytest.raises(DueReservationRejected, match="Path"):
        DisconnectedDueReservations(path)


def test_clean_due_reservation_still_survives_readonly_restart(tmp_path):
    path = tmp_path / "due.sqlite3"
    ledger = DisconnectedDueReservations(path)
    retained = ledger.witness()
    receipt = ledger.reserve_due(
        policy_sha256="a" * 64, due_at_ms=3,
        observed_now_ms=4, retained=retained,
    )
    assert receipt.execution_authorized is False
    assert receipt.notification_authorized is False
    assert receipt.automatic_replay_authorized is False
    reopened = DisconnectedDueReservations.reopen_with_witness(
        path, retained=receipt.witness,
    )
    assert reopened.witness() == receipt.witness
