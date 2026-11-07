"""Scalar custody of synthetic WRITE reservations under patched witness equality.

All checks are local SQLite fixtures. No ToolBackend or external action runs.
"""

from __future__ import annotations

import sqlite3

import pytest

from ark.agency import disconnected_write_slot_ledger as slots


def _claim(number: int) -> slots.DetachedWriteSlotClaim:
    plan = "plan_" + "a" * 64
    step = "step_" + f"{number:016x}"
    request = f"{number:064x}"
    return slots.DetachedWriteSlotClaim(
        slots.derive_disconnected_write_slot_id(plan, step, request),
        plan,
        step,
        request,
    )


def test_readonly_reopen_rejects_stale_tip_with_always_true_equality(
    tmp_path, monkeypatch,
):
    ledger = slots.DisconnectedWriteSlotLedger(tmp_path / "slots.sqlite", create=True)
    stale = slots.genesis_write_slot_witness()
    current = ledger.reserve_many((_claim(1),), retained=stale).witness

    with monkeypatch.context() as patch:
        patch.setattr(slots.WriteSlotLedgerWitness, "__eq__", lambda self, other: True)
        with pytest.raises(slots.WriteSlotLedgerRejected, match="stale"):
            ledger.inspect(retained=stale)
        observed = ledger.inspect(retained=current)
        assert (observed.count, observed.chain_sha256) == (
            current.count, current.chain_sha256,
        )


def test_stale_write_does_not_append_with_always_true_equality(
    tmp_path, monkeypatch,
):
    path = tmp_path / "slots.sqlite"
    ledger = slots.DisconnectedWriteSlotLedger(path, create=True)
    stale = slots.genesis_write_slot_witness()
    current = ledger.reserve_many((_claim(1),), retained=stale).witness

    with monkeypatch.context() as patch:
        patch.setattr(slots.WriteSlotLedgerWitness, "__eq__", lambda self, other: True)
        with pytest.raises(slots.WriteSlotLedgerRejected, match="stale"):
            ledger.reserve_many((_claim(2),), retained=stale)
    with sqlite3.connect(path) as conn:
        assert conn.execute("SELECT COUNT(*) FROM synthetic_write_slots").fetchone() == (1,)
    observed = ledger.inspect(retained=current)
    assert (observed.count, observed.chain_sha256) == (
        current.count, current.chain_sha256,
    )


def test_tampered_postinsert_tip_is_rolled_back_despite_equal_objects(
    tmp_path, monkeypatch,
):
    path = tmp_path / "slots.sqlite"
    ledger = slots.DisconnectedWriteSlotLedger(path, create=True)
    retained = slots.genesis_write_slot_witness()
    original = slots._inspect
    inspected = 0

    def dishonest_inspect(conn):
        nonlocal inspected
        inspected += 1
        actual = original(conn)
        if inspected == 2:
            forged = "0" * 64 if actual.chain_sha256 != "0" * 64 else "1" * 64
            return slots.WriteSlotLedgerWitness(actual.count, forged)
        return actual

    with monkeypatch.context() as patch:
        patch.setattr(slots.WriteSlotLedgerWitness, "__eq__", lambda self, other: True)
        patch.setattr(slots, "_inspect", dishonest_inspect)
        with pytest.raises(slots.WriteSlotLedgerRejected, match="append lost integrity"):
            ledger.reserve_many((_claim(1),), retained=retained)
    assert inspected == 2
    with sqlite3.connect(path) as conn:
        assert conn.execute("SELECT COUNT(*) FROM synthetic_write_slots").fetchone() == (0,)
    observed = ledger.inspect(retained=retained)
    assert (observed.count, observed.chain_sha256) == (
        retained.count, retained.chain_sha256,
    )


def test_valid_witness_roundtrip_does_not_depend_on_always_false_equality(
    tmp_path, monkeypatch,
):
    path = tmp_path / "slots.sqlite"
    ledger = slots.DisconnectedWriteSlotLedger(path, create=True)
    prior = slots.genesis_write_slot_witness()
    with monkeypatch.context() as patch:
        patch.setattr(slots.WriteSlotLedgerWitness, "__eq__", lambda self, other: False)
        initial = ledger.inspect(retained=prior)
        assert initial.count == prior.count
        receipt = ledger.reserve_many((_claim(1),), retained=prior)
        assert receipt.witness.count == 1
        reopened = slots.DisconnectedWriteSlotLedger(path).inspect(
            retained=receipt.witness,
        )
        assert reopened.count == receipt.witness.count
        assert reopened.chain_sha256 == receipt.witness.chain_sha256
        assert receipt.dispatch_authorized is False
        assert receipt.automatic_replay_authorized is False
