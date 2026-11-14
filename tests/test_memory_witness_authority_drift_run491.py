"""Memory witness restart and CAS must reject callback-era authority drift."""

from __future__ import annotations

from pathlib import Path

import pytest

from ark.memory import disconnected_witness_ledger as memory
from ark.memory.atomic_epoch_review import AtomicMemoryEpochReview


def _epoch() -> AtomicMemoryEpochReview:
    return AtomicMemoryEpochReview(
        ("a" * 64,), (1,), (1,), (1,), "b" * 64, "c" * 64,
    )


def test_existing_restart_rejects_equal_path_rebound_in_startup_snapshot(
    tmp_path, monkeypatch,
):
    path = tmp_path / "retained.sqlite"
    memory.DisconnectedMemoryWitnessLedger(path, create=True)
    holder = {}

    class CapturedLedger(memory.DisconnectedMemoryWitnessLedger):
        def _open(self, *, read_only):
            holder["ledger"] = self
            return super()._open(read_only=read_only)

    original = memory._inspect

    def replace_source(conn):
        result = original(conn)
        ledger = holder["ledger"]
        replacement = Path(str(ledger._path))
        assert replacement == ledger._path and replacement is not ledger._path
        ledger._path = replacement
        return result

    monkeypatch.setattr(memory, "_inspect", replace_source)
    with pytest.raises(memory.MemoryWitnessLedgerRejected, match="startup path changed"):
        CapturedLedger(path)
    monkeypatch.setattr(memory, "_inspect", original)
    assert memory.DisconnectedMemoryWitnessLedger(path).inspect(
        retained=memory.genesis_memory_ledger_witness(),
    ).epochs == 0


def test_append_rejects_authority_spoof_inside_transaction_before_commit(
    tmp_path, monkeypatch,
):
    path = tmp_path / "retained.sqlite"
    ledger = memory.DisconnectedMemoryWitnessLedger(path, create=True)
    genesis = memory.genesis_memory_ledger_witness()
    original = memory._inspect
    old_property = memory.MemoryLedgerWitness.dispatch_authorized
    count = 0

    def spoof_after_read(conn):
        nonlocal count
        result = original(conn)
        count += 1
        if count == 1:
            monkeypatch.setattr(
                memory.MemoryLedgerWitness,
                "dispatch_authorized",
                property(lambda self: True),
            )
        return result

    monkeypatch.setattr(memory, "_inspect", spoof_after_read)
    with pytest.raises(memory.MemoryWitnessLedgerRejected, match="inputs changed"):
        ledger.append(_epoch(), retained=genesis)
    monkeypatch.setattr(memory, "_inspect", original)
    monkeypatch.setattr(memory.MemoryLedgerWitness, "dispatch_authorized", old_property)
    assert ledger.inspect(retained=genesis) == genesis
    assert genesis.memory_disclosure_authorized is False
    assert genesis.dispatch_authorized is False
