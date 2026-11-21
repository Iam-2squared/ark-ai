"""Synthetic WRITE-slot inputs must reject executable class descriptors first.

A frozen dataclass does not protect class-level slots or lookup hooks. These
fixtures never dispatch a backend or prove any external action/authorization.
"""

from __future__ import annotations

import sqlite3

import pytest

from ark.agency import disconnected_write_slot_ledger as slots


def _fixture(tmp_path):
    path = tmp_path / "disconnected-write-slots.sqlite"
    ledger = slots.DisconnectedWriteSlotLedger(path, create=True)
    witness = slots.genesis_write_slot_witness()
    plan = "plan_" + "1" * 64
    step = "step_" + "2" * 16
    request = "3" * 64
    claim = slots.DetachedWriteSlotClaim(
        slots.derive_disconnected_write_slot_id(plan, step, request),
        plan, step, request,
    )
    return ledger, witness, claim, path


def _forged_descriptor(name, calls):
    if name == "__getattr__":
        def forged(self, attr):
            calls.append(attr)
            raise AssertionError("unexpected executable lookup")
    else:
        def forged(self):
            calls.append(name)
            raise AssertionError("unexpected executable field getter")
        return property(forged)
    return forged


@pytest.mark.parametrize(
    "field",
    ("count", "chain_sha256", "__getattr__"),
)
@pytest.mark.parametrize("operation", ("inspect", "reserve"))
def test_witness_descriptor_must_be_original_before_private_sqlite(
    tmp_path, monkeypatch, field, operation,
):
    ledger, witness, claim, path = _fixture(tmp_path)
    called = []
    replacement = _forged_descriptor(field, called)
    with monkeypatch.context() as patch:
        patch.setattr(slots.WriteSlotLedgerWitness, field, replacement, raising=False)
        with pytest.raises(slots.WriteSlotLedgerRejected, match="constructor or authority"):
            if operation == "inspect":
                ledger.inspect(retained=witness)
            else:
                ledger.reserve_many((claim,), retained=witness)
    assert called == []
    with sqlite3.connect(path) as conn:
        assert conn.execute(
            "SELECT COUNT(*) FROM synthetic_write_slots"
        ).fetchone() == (0,)
    assert ledger.inspect(retained=witness) == witness


@pytest.mark.parametrize(
    "field",
    (
        "slot_id", "plan_id", "step_id", "request_sha256",
        "__getattr__",
    ),
)
def test_claim_descriptor_must_be_original_before_write_lock(
    tmp_path, monkeypatch, field,
):
    ledger, witness, claim, path = _fixture(tmp_path)
    called = []
    with monkeypatch.context() as patch:
        patch.setattr(
            slots.DetachedWriteSlotClaim, field,
            _forged_descriptor(field, called), raising=False,
        )
        with pytest.raises(slots.WriteSlotLedgerRejected, match="constructor or authority"):
            ledger.reserve_many((claim,), retained=witness)
    assert called == []
    with sqlite3.connect(path) as conn:
        assert conn.execute(
            "SELECT COUNT(*) FROM synthetic_write_slots"
        ).fetchone() == (0,)
    assert ledger.inspect(retained=witness) == witness


def test_claim_slot_changed_during_row_hash_rolls_back_before_commit(
    tmp_path, monkeypatch,
):
    ledger, witness, claim, path = _fixture(tmp_path)
    native = slots._hash
    called = []
    triggered = []
    with monkeypatch.context() as patch:
        def replace_at_row_hash(fields):
            digest = native(fields)
            if fields[0] == "row":
                triggered.append(True)
                patch.setattr(
                    slots.DetachedWriteSlotClaim, "slot_id",
                    _forged_descriptor("slot_id", called),
                )
            return digest

        patch.setattr(slots, "_hash", replace_at_row_hash)
        with pytest.raises(slots.WriteSlotLedgerRejected, match="constructor or authority"):
            ledger.reserve_many((claim,), retained=witness)
    assert triggered == [True]
    assert called == []
    with sqlite3.connect(path) as conn:
        assert conn.execute(
            "SELECT COUNT(*) FROM synthetic_write_slots"
        ).fetchone() == (0,)
    assert ledger.inspect(retained=witness) == witness


def test_original_slots_still_reserve_only_a_synthetic_occurrence(tmp_path):
    ledger, retained, claim, path = _fixture(tmp_path)
    receipt = ledger.reserve_many((claim,), retained=retained)
    assert receipt.added_count == 1
    assert receipt.dispatch_authorized is False
    assert receipt.automatic_replay_authorized is False
    assert receipt.exact_once_external_effect_proven is False
    assert slots.DisconnectedWriteSlotLedger(path).inspect(
        retained=receipt.witness,
    ) == receipt.witness
