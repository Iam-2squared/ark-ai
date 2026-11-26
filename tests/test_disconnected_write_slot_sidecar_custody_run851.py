"""Synthetic WRITE reservations refuse aliased/orphaned SQLite sidecars.

Disposable fixture paths only; no real executor or external WRITE permission.
"""

from __future__ import annotations

import os

import pytest

from ark.agency.disconnected_write_slot_ledger import (
    DetachedWriteSlotClaim,
    DisconnectedWriteSlotLedger,
    WriteSlotLedgerRejected,
    derive_disconnected_write_slot_id,
    genesis_write_slot_witness,
)


def _claim() -> DetachedWriteSlotClaim:
    plan = "plan_" + "1" * 64
    step = "step_" + "2" * 16
    request = "3" * 64
    return DetachedWriteSlotClaim(
        derive_disconnected_write_slot_id(plan, step, request),
        plan, step, request,
    )


@pytest.mark.parametrize("suffix", ("-wal", "-shm", "-journal"))
def test_existing_ledger_rejects_nonfile_sidecar_before_sqlite(tmp_path, suffix):
    path = tmp_path / "synthetic.db"
    ledger = DisconnectedWriteSlotLedger(path, create=True)
    prior = genesis_write_slot_witness()
    sidecar = path.with_name(path.name + suffix)
    sidecar.mkdir()
    with pytest.raises(WriteSlotLedgerRejected, match="sidecar"):
        DisconnectedWriteSlotLedger(path)
    with pytest.raises(WriteSlotLedgerRejected, match="sidecar"):
        ledger.inspect(retained=prior)
    with pytest.raises(WriteSlotLedgerRejected, match="sidecar"):
        ledger.reserve_many((_claim(),), retained=prior)
    sidecar.rmdir()
    assert ledger.inspect(retained=prior) == prior


@pytest.mark.parametrize("suffix", ("-wal", "-shm", "-journal"))
def test_new_ledger_refuses_orphan_sidecar_without_creating_db(tmp_path, suffix):
    path = tmp_path / "not-created.db"
    sidecar = path.with_name(path.name + suffix)
    sidecar.write_bytes(b"fixture-only")
    with pytest.raises(WriteSlotLedgerRejected, match="sidecar"):
        DisconnectedWriteSlotLedger(path, create=True)
    assert not path.exists()
    assert sidecar.read_bytes() == b"fixture-only"


@pytest.mark.parametrize("suffix", ("-wal", "-shm", "-journal"))
def test_reopen_refuses_hardlinked_sidecar(tmp_path, suffix):
    path = tmp_path / "synthetic.db"
    DisconnectedWriteSlotLedger(path, create=True)
    other = tmp_path / "other.bin"
    other.write_bytes(b"must-not-be-used")
    sidecar = path.with_name(path.name + suffix)
    try:
        os.link(other, sidecar)
    except OSError:
        pytest.skip("hardlinks are unavailable on this test filesystem")
    with pytest.raises(WriteSlotLedgerRejected, match="sidecar"):
        DisconnectedWriteSlotLedger(path)
    assert other.read_bytes() == b"must-not-be-used"


@pytest.mark.parametrize("suffix", ("-wal", "-shm", "-journal"))
def test_reopen_refuses_symlinked_sidecar(tmp_path, suffix):
    path = tmp_path / "synthetic.db"
    DisconnectedWriteSlotLedger(path, create=True)
    other = tmp_path / "other.bin"
    other.write_bytes(b"must-not-be-followed")
    sidecar = path.with_name(path.name + suffix)
    try:
        sidecar.symlink_to(other)
    except (OSError, NotImplementedError):
        pytest.skip("symlinks are unavailable on this test filesystem")
    with pytest.raises(WriteSlotLedgerRejected, match="sidecar"):
        DisconnectedWriteSlotLedger(path)
    assert other.read_bytes() == b"must-not-be-followed"


def test_normal_write_slot_fixture_still_reserves_and_reopens(tmp_path):
    path = tmp_path / "synthetic.db"
    ledger = DisconnectedWriteSlotLedger(path, create=True)
    initial = genesis_write_slot_witness()
    receipt = ledger.reserve_many((_claim(),), retained=initial)
    assert receipt.added_count == 1
    assert receipt.witness.count == 1
    assert receipt.dispatch_authorized is False
    assert receipt.automatic_replay_authorized is False
    assert DisconnectedWriteSlotLedger(path).inspect(
        retained=receipt.witness,
    ) == receipt.witness
