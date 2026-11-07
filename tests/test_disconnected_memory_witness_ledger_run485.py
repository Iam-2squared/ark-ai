"""Offline witness ledger: local CAS and rollback evidence, never action authority."""

from __future__ import annotations

import sqlite3
from dataclasses import replace

import pytest

import ark.memory.disconnected_witness_ledger as ledger
from ark.memory.atomic_epoch_review import AtomicMemoryEpochReview
from ark.memory.contracts import MemorySchemaError


def _epoch(count=1, content="c", scope="a"):
    return AtomicMemoryEpochReview(
        (scope * 64,), (1,), (count,), (count,), "b" * 64, content * 64,
    )


def _new(tmp_path):
    path = tmp_path / "witness.sqlite"
    return path, ledger.DisconnectedMemoryWitnessLedger(path, create=True)


def test_genesis_and_restart_are_read_only_and_non_authorizing(tmp_path):
    path, store = _new(tmp_path)
    genesis = ledger.genesis_memory_ledger_witness()
    assert store.inspect(retained=genesis) == genesis
    reopened = ledger.DisconnectedMemoryWitnessLedger(path)
    assert reopened.inspect(retained=genesis) == genesis
    assert genesis.custody_authenticated is False
    assert genesis.independent_writer_proven is False
    assert genesis.historical_prefix_proven is False
    assert genesis.memory_disclosure_authorized is False
    assert genesis.dispatch_authorized is False


def test_append_and_restart_preserve_external_witness_tip(tmp_path):
    path, store = _new(tmp_path)
    first = store.append(_epoch(), retained=ledger.genesis_memory_ledger_witness())
    second = store.append(_epoch(2, "d"), retained=first)
    assert second.epochs == 2
    assert first.chain_sha256 != second.chain_sha256
    reopened = ledger.DisconnectedMemoryWitnessLedger(path)
    assert reopened.inspect(retained=second) == second
    with pytest.raises(ledger.MemoryWitnessLedgerRejected, match="retained witness mismatch"):
        reopened.inspect(retained=first)


def test_stale_cas_rejected_after_concurrent_instance_appends(tmp_path):
    path, store = _new(tmp_path)
    other = ledger.DisconnectedMemoryWitnessLedger(path)
    old = ledger.genesis_memory_ledger_witness()
    current = store.append(_epoch(), retained=old)
    with pytest.raises(ledger.MemoryWitnessLedgerRejected, match="stale witness CAS"):
        other.append(_epoch(), retained=old)
    assert other.inspect(retained=current) == current


def test_unchanged_observation_is_explicitly_non_authenticating(tmp_path):
    _, store = _new(tmp_path)
    first = store.append(_epoch(), retained=ledger.genesis_memory_ledger_witness())
    second = store.append(_epoch(), retained=first)
    assert second.epochs == 2
    assert second.custody_authenticated is False


@pytest.mark.parametrize("candidate", [
    _epoch(0, "d"), _epoch(2, "d", "f"), _epoch(1, "d"),
])
def test_event_regression_scope_drift_or_undocumented_edit_rejected(tmp_path, candidate):
    _, store = _new(tmp_path)
    first = store.append(_epoch(), retained=ledger.genesis_memory_ledger_witness())
    with pytest.raises(MemorySchemaError):
        store.append(candidate, retained=first)
    assert store.inspect(retained=first) == first


@pytest.mark.parametrize("field,value", [
    ("epochs", True), ("epochs", -1), ("epochs", 257),
    ("chain_sha256", "not-a-hash"), ("chain_sha256", "Z" * 64),
])
def test_invalid_retained_witness_rejected(tmp_path, field, value):
    _, store = _new(tmp_path)
    bad = replace(ledger.genesis_memory_ledger_witness(), **{field: value})
    with pytest.raises(ledger.MemoryWitnessLedgerRejected):
        store.inspect(retained=bad)
    with pytest.raises(ledger.MemoryWitnessLedgerRejected):
        store.append(_epoch(), retained=bad)


@pytest.mark.parametrize("column,new_value", [
    ("payload_json", "[]"), ("status", "VERIFIED"),
    ("chain_sha256", "f" * 64),
])
def test_persisted_row_tamper_fails_closed(tmp_path, column, new_value):
    path, store = _new(tmp_path)
    first = store.append(_epoch(), retained=ledger.genesis_memory_ledger_witness())
    with sqlite3.connect(path) as conn:
        conn.execute(
            f"UPDATE retained_memory_epochs SET {column}=? WHERE seq=1",
            (new_value,),
        )
    with pytest.raises(ledger.MemoryWitnessLedgerRejected):
        store.inspect(retained=first)


def test_schema_extension_fails_closed_without_repair(tmp_path):
    path, store = _new(tmp_path)
    with sqlite3.connect(path) as conn:
        conn.execute("CREATE TABLE unexpected (id INTEGER)")
    with pytest.raises(ledger.MemoryWitnessLedgerRejected, match="schema drift"):
        store.inspect(retained=ledger.genesis_memory_ledger_witness())


def test_create_only_refuses_existing_ledger(tmp_path):
    path, _ = _new(tmp_path)
    with pytest.raises(ledger.MemoryWitnessLedgerRejected):
        ledger.DisconnectedMemoryWitnessLedger(path, create=True)


def test_missing_ledger_does_not_get_recreated(tmp_path):
    path, store = _new(tmp_path)
    path.unlink()
    with pytest.raises(ledger.MemoryWitnessLedgerRejected, match="missing retained ledger"):
        store.inspect(retained=ledger.genesis_memory_ledger_witness())
    assert not path.exists()


def test_source_observation_mutation_during_serialization_rejected(tmp_path, monkeypatch):
    _, store = _new(tmp_path)
    review = _epoch()
    original = ledger._payload

    def adversarial(value):
        payload = original(value)
        object.__setattr__(value, "event_counts", (2,))
        return payload

    monkeypatch.setattr(ledger, "_payload", adversarial)
    with pytest.raises(ledger.MemoryWitnessLedgerRejected, match="inputs changed"):
        store.append(review, retained=ledger.genesis_memory_ledger_witness())


def test_witness_budget_blocks_additional_observations(tmp_path, monkeypatch):
    _, store = _new(tmp_path)
    first = store.append(_epoch(), retained=ledger.genesis_memory_ledger_witness())
    monkeypatch.setattr(ledger, "_MAX_EPOCHS", 1)
    with pytest.raises(ledger.MemoryWitnessLedgerRejected, match="budget exceeded"):
        store.append(_epoch(2, "d"), retained=first)
    assert store.inspect(retained=first) == first


def test_only_hashes_and_count_metadata_are_stored(tmp_path):
    path, store = _new(tmp_path)
    review = _epoch()
    store.append(review, retained=ledger.genesis_memory_ledger_witness())
    raw = path.read_bytes()
    assert b"memory-content-secret" not in raw
    with sqlite3.connect(path) as conn:
        payload = conn.execute(
            "SELECT payload_json FROM retained_memory_epochs"
        ).fetchone()[0]
    assert "c" * 64 in payload
    assert "memory-content-secret" not in payload
