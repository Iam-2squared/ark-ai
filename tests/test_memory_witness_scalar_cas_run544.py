"""Disconnected Memory witness CAS must ignore replaceable object equality.

Only synthetic SQLite epoch digests are used; no Memory v1 content or action.
"""

from __future__ import annotations

import sqlite3

import pytest

from ark.memory import disconnected_witness_ledger as memory
from ark.memory.atomic_epoch_review import AtomicMemoryEpochReview


def _epoch(count: int = 1, content: str = "c") -> AtomicMemoryEpochReview:
    return AtomicMemoryEpochReview(
        ("a" * 64,), (1,), (count,), (count,), "b" * 64, content * 64,
    )


def test_memory_witness_stale_read_rejected_even_if_equality_always_true(
    tmp_path, monkeypatch,
):
    path = tmp_path / "epochs.sqlite"
    store = memory.DisconnectedMemoryWitnessLedger(path, create=True)
    stale = memory.genesis_memory_ledger_witness()
    current = store.append(_epoch(), retained=stale)

    with monkeypatch.context() as patch:
        patch.setattr(memory.MemoryLedgerWitness, "__eq__", lambda self, other: True)
        with pytest.raises(memory.MemoryWitnessLedgerRejected, match="retained witness mismatch"):
            store.inspect(retained=stale)
        observed = store.inspect(retained=current)
        assert (observed.epochs, observed.chain_sha256) == (
            current.epochs, current.chain_sha256,
        )


def test_memory_witness_stale_append_rejected_even_if_equality_always_true(
    tmp_path, monkeypatch,
):
    path = tmp_path / "epochs.sqlite"
    store = memory.DisconnectedMemoryWitnessLedger(path, create=True)
    stale = memory.genesis_memory_ledger_witness()
    current = store.append(_epoch(), retained=stale)

    with monkeypatch.context() as patch:
        patch.setattr(memory.MemoryLedgerWitness, "__eq__", lambda self, other: True)
        with pytest.raises(memory.MemoryWitnessLedgerRejected, match="stale witness CAS tip"):
            store.append(_epoch(2, "d"), retained=stale)
    with sqlite3.connect(path) as conn:
        assert conn.execute("SELECT COUNT(*) FROM retained_memory_epochs").fetchone() == (1,)
    assert store.inspect(retained=current).epochs == 1


def test_memory_witness_postinsert_forged_tip_rolls_back_before_commit(
    tmp_path, monkeypatch,
):
    path = tmp_path / "epochs.sqlite"
    store = memory.DisconnectedMemoryWitnessLedger(path, create=True)
    old = memory.genesis_memory_ledger_witness()
    native = memory._inspect
    calls = 0

    def forged_second_inspection(conn):
        nonlocal calls
        calls += 1
        witness, review = native(conn)
        if calls == 2:
            different = "0" * 64 if witness.chain_sha256 != "0" * 64 else "1" * 64
            return memory.MemoryLedgerWitness(witness.epochs, different), review
        return witness, review

    with monkeypatch.context() as patch:
        patch.setattr(memory.MemoryLedgerWitness, "__eq__", lambda self, other: True)
        patch.setattr(memory, "_inspect", forged_second_inspection)
        with pytest.raises(memory.MemoryWitnessLedgerRejected, match="witness insert changed"):
            store.append(_epoch(), retained=old)
    assert calls == 2
    with sqlite3.connect(path) as conn:
        assert conn.execute("SELECT COUNT(*) FROM retained_memory_epochs").fetchone() == (0,)
    assert store.inspect(retained=old).epochs == 0


def test_memory_witness_valid_roundtrip_ignores_always_false_equality(
    tmp_path, monkeypatch,
):
    path = tmp_path / "epochs.sqlite"
    store = memory.DisconnectedMemoryWitnessLedger(path, create=True)
    old = memory.genesis_memory_ledger_witness()
    with monkeypatch.context() as patch:
        patch.setattr(memory.MemoryLedgerWitness, "__eq__", lambda self, other: False)
        assert store.inspect(retained=old).epochs == 0
        first = store.append(_epoch(), retained=old)
        assert first.epochs == 1
        assert memory.DisconnectedMemoryWitnessLedger(path).inspect(
            retained=first,
        ).chain_sha256 == first.chain_sha256
        assert first.dispatch_authorized is False
        assert first.memory_disclosure_authorized is False
