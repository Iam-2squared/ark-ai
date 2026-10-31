"""Independent retained reservation witnesses are checked in one read snapshot.

All storage is disposable SQLite and all ToolBackend implementations refuse
execution. Local hash continuity is never clock/issuer or action attestation.
"""

import hashlib
import sqlite3

import pytest

import ark.agency.synthetic_occurrence_continuity_review as module
from ark.agency.contracts import Effect, OneShotAuthorization, ToolCall
from ark.agency.durable_occurrence_review import (
    SyntheticOccurrenceStore,
    SyntheticReplayRejected,
)
from ark.agency.registry import ToolRegistration, ToolRegistry


class NoBackend:
    def execute(self, _call):
        raise AssertionError("ledger witness must never dispatch")


def _reserve(store, identity, *, now=10):
    call = ToolCall("offline", "mock.write", "local", {"n": 1})
    registry = ToolRegistry((
        ToolRegistration("offline", "mock.write", Effect.WRITE, "fixture", NoBackend()),
    ))
    store.reserve_synthetic(
        registry, call,
        OneShotAuthorization("token-" + identity, call.request_id, 1000),
        occurrence_id="occ_" + hashlib.sha256(identity.encode()).hexdigest(),
        now_ms=now,
    )


def _clone_rows(rows):
    copied = tuple(list(rows))
    assert copied == rows and copied is not rows
    return copied


def test_retained_same_snapshot_review_accepts_exact_history_extension(tmp_path):
    path = tmp_path / "occ.sqlite"
    store = SyntheticOccurrenceStore(path)
    _reserve(store, "one")
    old = module.read_synthetic_ledger_witness(path)
    _reserve(store, "two", now=11)
    later = module.read_synthetic_ledger_witness(path, retained=old)
    assert len(old.row_hashes) == 1
    assert len(later.row_hashes) == 2
    assert later == module.read_synthetic_ledger_witness(path, retained=old)


def test_retained_same_snapshot_review_rejects_erased_history(tmp_path):
    path = tmp_path / "occ.sqlite"
    store = SyntheticOccurrenceStore(path)
    _reserve(store, "one")
    old = module.read_synthetic_ledger_witness(path)
    with sqlite3.connect(path) as conn:
        conn.execute("DELETE FROM synthetic_occurrence_reservations")
    assert module.read_synthetic_ledger_witness(path).row_hashes == ()
    with pytest.raises(SyntheticReplayRejected, match="retained reservation history changed"):
        module.read_synthetic_ledger_witness(path, retained=old)


def test_retained_witness_equal_carrier_swap_mid_row_hash_is_refused(
    tmp_path, monkeypatch,
):
    path = tmp_path / "occ.sqlite"
    store = SyntheticOccurrenceStore(path)
    _reserve(store, "one")
    kept = module.read_synthetic_ledger_witness(path)
    _reserve(store, "two", now=11)
    digest = module._digest
    changed = []

    def swap(label, data):
        result = digest(label, data)
        if label == "ARK-reservation-row-v1" and not changed:
            object.__setattr__(kept, "row_hashes", _clone_rows(kept.row_hashes))
            changed.append(True)
        return result

    monkeypatch.setattr(module, "_digest", swap)
    with pytest.raises(SyntheticReplayRejected, match="witness changed"):
        module.read_synthetic_ledger_witness(path, retained=kept)
    assert changed


def test_retained_witness_equal_swap_during_final_digest_is_refused(
    tmp_path, monkeypatch,
):
    path = tmp_path / "occ.sqlite"
    store = SyntheticOccurrenceStore(path)
    _reserve(store, "one")
    kept = module.read_synthetic_ledger_witness(path)
    digest = module._digest
    changed = []

    def swap(label, data):
        result = digest(label, data)
        if label == "ARK-ledger-v1" and not changed:
            object.__setattr__(kept, "row_hashes", _clone_rows(kept.row_hashes))
            changed.append(True)
        return result

    monkeypatch.setattr(module, "_digest", swap)
    with pytest.raises(SyntheticReplayRejected, match="witness changed"):
        module.read_synthetic_ledger_witness(path, retained=kept)
    assert changed


def test_direct_continuity_catches_other_witness_mutated_during_integrity(
    tmp_path, monkeypatch,
):
    path = tmp_path / "occ.sqlite"
    store = SyntheticOccurrenceStore(path)
    _reserve(store, "one")
    retained = module.read_synthetic_ledger_witness(path)
    current = module.read_synthetic_ledger_witness(path)
    assert module.assert_synthetic_history_continues(retained, current) is None
    original = module.SyntheticLedgerWitness.assert_integrity

    def mutate_other(self):
        original(self)
        if self is retained:
            object.__setattr__(current, "row_hashes", _clone_rows(current.row_hashes))

    monkeypatch.setattr(module.SyntheticLedgerWitness, "assert_integrity", mutate_other)
    with pytest.raises(SyntheticReplayRejected, match="witness changed"):
        module.assert_synthetic_history_continues(retained, current)


def test_oversize_retained_witness_is_rejected_before_disk_access(tmp_path):
    hashes = tuple(f"{index:064x}" for index in range(10_001))
    witness = module.SyntheticLedgerWitness(
        hashes, "synthetic_ledger_" + module._digest("ARK-ledger-v1", hashes),
    )
    with pytest.raises(SyntheticReplayRejected, match="witness integrity"):
        module.read_synthetic_ledger_witness(tmp_path / "absent.sqlite", retained=witness)


def test_nonexact_retained_rejected_before_disk_access(tmp_path):
    with pytest.raises(SyntheticReplayRejected, match="exact synthetic retained"):
        module.read_synthetic_ledger_witness(tmp_path / "missing.sqlite", retained={})


def test_unretained_read_never_creates_missing_database(tmp_path):
    path = tmp_path / "missing.sqlite"
    with pytest.raises(sqlite3.OperationalError):
        module.read_synthetic_ledger_witness(path)
    assert not path.exists()
