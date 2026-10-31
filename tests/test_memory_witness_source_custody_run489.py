"""Retained Memory witness inspection and CAS pin the exact source carrier."""

from __future__ import annotations

from pathlib import Path

import pytest

import ark.memory.disconnected_witness_ledger as witness_ledger
from ark.memory.atomic_epoch_review import AtomicMemoryEpochReview


def epoch():
    return AtomicMemoryEpochReview(
        ("a" * 64,), (1,), (1,), (1,), "b" * 64, "c" * 64,
    )


def setup(tmp_path):
    path = tmp_path / "memory-witness.sqlite"
    return path, witness_ledger.DisconnectedMemoryWitnessLedger(path, create=True)


def test_existing_ledger_restart_still_accepts_exact_retained_tip(tmp_path):
    path, first = setup(tmp_path)
    origin = witness_ledger.genesis_memory_ledger_witness()
    saved = first.append(epoch(), retained=origin)
    reopened = witness_ledger.DisconnectedMemoryWitnessLedger(path)
    assert reopened.inspect(retained=saved) == saved
    assert saved.custody_authenticated is False
    assert saved.dispatch_authorized is False


def test_inspect_rejects_equal_valued_path_rebound_during_sqlite_review(
    tmp_path, monkeypatch,
):
    path, store = setup(tmp_path)
    original = witness_ledger._inspect

    def swap(conn):
        result = original(conn)
        store._path = Path(str(path))
        return result

    monkeypatch.setattr(witness_ledger, "_inspect", swap)
    with pytest.raises(witness_ledger.MemoryWitnessLedgerRejected, match="carrier changed"):
        store.inspect(retained=witness_ledger.genesis_memory_ledger_witness())
    assert witness_ledger.DisconnectedMemoryWitnessLedger(path).inspect(
        retained=witness_ledger.genesis_memory_ledger_witness(),
    ) == witness_ledger.genesis_memory_ledger_witness()


def test_inspect_rejects_retained_witness_rewrite_during_review(tmp_path, monkeypatch):
    _, store = setup(tmp_path)
    retained = witness_ledger.genesis_memory_ledger_witness()
    original = witness_ledger._inspect

    def tamper(conn):
        result = original(conn)
        object.__setattr__(retained, "chain_sha256", "f" * 64)
        return result

    monkeypatch.setattr(witness_ledger, "_inspect", tamper)
    with pytest.raises(witness_ledger.MemoryWitnessLedgerRejected, match="carrier changed"):
        store.inspect(retained=retained)


def test_append_rejects_source_rebound_during_serialization(tmp_path, monkeypatch):
    path, store = setup(tmp_path)
    original_payload = witness_ledger._payload

    def tamper(review):
        payload = original_payload(review)
        store._path = Path(str(path))
        return payload

    monkeypatch.setattr(witness_ledger, "_payload", tamper)
    with pytest.raises(witness_ledger.MemoryWitnessLedgerRejected, match="inputs changed"):
        store.append(epoch(), retained=witness_ledger.genesis_memory_ledger_witness())
    assert witness_ledger.DisconnectedMemoryWitnessLedger(path).inspect(
        retained=witness_ledger.genesis_memory_ledger_witness(),
    ).epochs == 0


def test_append_rejects_source_rebound_inside_write_transaction(tmp_path, monkeypatch):
    path, store = setup(tmp_path)
    original = witness_ledger._inspect

    def tamper(conn):
        result = original(conn)
        store._path = Path(str(path))
        return result

    monkeypatch.setattr(witness_ledger, "_inspect", tamper)
    with pytest.raises(witness_ledger.MemoryWitnessLedgerRejected, match="inputs changed"):
        store.append(epoch(), retained=witness_ledger.genesis_memory_ledger_witness())
    assert witness_ledger.DisconnectedMemoryWitnessLedger(path).inspect(
        retained=witness_ledger.genesis_memory_ledger_witness(),
    ).epochs == 0


def test_inspect_rejects_spoofed_observed_witness_type(tmp_path, monkeypatch):
    _, store = setup(tmp_path)
    original = witness_ledger._inspect

    def falsify(conn):
        _, previous = original(conn)
        return object(), previous

    monkeypatch.setattr(witness_ledger, "_inspect", falsify)
    with pytest.raises(witness_ledger.MemoryWitnessLedgerRejected, match="invalid retained"):
        store.inspect(retained=witness_ledger.genesis_memory_ledger_witness())
