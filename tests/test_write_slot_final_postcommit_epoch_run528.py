"""Post-COMMIT synthetic WRITE reservation custody; no ToolBackend execution."""

from __future__ import annotations

import sqlite3

import pytest

from ark.agency import disconnected_write_slot_ledger as slots


def _claim() -> slots.DetachedWriteSlotClaim:
    plan = "plan_" + "a" * 64
    step = "step_" + "b" * 16
    request = "c" * 64
    return slots.DetachedWriteSlotClaim(
        slots.derive_disconnected_write_slot_id(plan, step, request),
        plan, step, request,
    )


@pytest.mark.parametrize("field", [
    "receipt_count", "witness_count", "witness_hash", "retained_hash",
])
def test_last_false_getter_cannot_mutate_postcommit_receipt_carriers(
    tmp_path, monkeypatch, field,
):
    ledger = slots.DisconnectedWriteSlotLedger(tmp_path / "writes.sqlite", create=True)
    old = slots.genesis_write_slot_witness()

    def change(self):
        if field == "receipt_count":
            object.__setattr__(self, "added_count", 2)
        elif field == "witness_count":
            object.__setattr__(self.witness, "count", 2)
        elif field == "witness_hash":
            object.__setattr__(self.witness, "chain_sha256", "f" * 64)
        else:
            object.__setattr__(old, "chain_sha256", "f" * 64)
        return False

    monkeypatch.setattr(
        slots.WriteSlotReservationReceipt, "owner_or_consent_verified",
        property(change),
    )
    with pytest.raises(slots.WriteSlotLedgerRejected, match="post-commit|carriers"):
        ledger.reserve_many((_claim(),), retained=old)
    # The COMMIT happened. This is not a rollback or permission to retry it.
    with sqlite3.connect(ledger._path) as conn:
        assert conn.execute("SELECT COUNT(*) FROM synthetic_write_slots").fetchone() == (1,)


def test_last_false_getter_cannot_alter_persisted_slot_after_commit(
    tmp_path, monkeypatch,
):
    ledger = slots.DisconnectedWriteSlotLedger(tmp_path / "writes.sqlite", create=True)
    old = slots.genesis_write_slot_witness()

    def change(_self):
        with sqlite3.connect(ledger._path) as conn:
            conn.execute(
                "UPDATE synthetic_write_slots SET request_sha256=? WHERE seq=1",
                ("f" * 64,),
            )
        return False

    monkeypatch.setattr(
        slots.WriteSlotReservationReceipt, "owner_or_consent_verified",
        property(change),
    )
    with pytest.raises(slots.WriteSlotLedgerRejected, match="post-commit|persisted"):
        ledger.reserve_many((_claim(),), retained=old)
    with sqlite3.connect(ledger._path) as conn:
        assert conn.execute("SELECT COUNT(*) FROM synthetic_write_slots").fetchone() == (1,)


def test_last_false_getter_cannot_rebind_its_authority_descriptor(
    tmp_path, monkeypatch,
):
    ledger = slots.DisconnectedWriteSlotLedger(tmp_path / "writes.sqlite", create=True)
    old = slots.genesis_write_slot_witness()
    invocations = 0

    def rebind(_self):
        nonlocal invocations
        invocations += 1
        if invocations == 2:
            monkeypatch.setattr(
                slots.WriteSlotReservationReceipt, "owner_or_consent_verified",
                property(lambda self: False),
            )
        return False

    monkeypatch.setattr(
        slots.WriteSlotReservationReceipt, "owner_or_consent_verified",
        property(rebind),
    )
    with pytest.raises(slots.WriteSlotLedgerRejected, match="receipt epoch"):
        ledger.reserve_many((_claim(),), retained=old)
    assert invocations == 2
    with sqlite3.connect(ledger._path) as conn:
        assert conn.execute("SELECT COUNT(*) FROM synthetic_write_slots").fetchone() == (1,)


def test_normal_receipt_remains_reopenable_and_never_dispatch_authority(tmp_path):
    path = tmp_path / "writes.sqlite"
    ledger = slots.DisconnectedWriteSlotLedger(path, create=True)
    old = slots.genesis_write_slot_witness()
    result = ledger.reserve_many((_claim(),), retained=old)
    assert result.added_count == result.witness.count == 1
    assert slots.DisconnectedWriteSlotLedger(path).inspect(
        retained=result.witness,
    ) == result.witness
    assert result.dispatch_authorized is False
    assert result.automatic_replay_authorized is False
    with pytest.raises(slots.WriteSlotLedgerRejected, match="stale"):
        ledger.reserve_many((_claim(),), retained=old)
