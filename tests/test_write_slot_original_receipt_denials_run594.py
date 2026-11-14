"""Original post-COMMIT WRITE-slot denial properties must not be replaceable.

The SQLite reservation may have committed even when the returned synthetic
receipt is rejected. It is NOT a dispatch approval or retry authorization.
"""

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


@pytest.mark.parametrize("field", slots._RECEIPT_DENIALS)
def test_false_only_receipt_getter_substitution_is_a_new_authority_epoch(
    tmp_path, monkeypatch, field,
):
    ledger = slots.DisconnectedWriteSlotLedger(tmp_path / "write-slots.sqlite", create=True)
    retained = slots.genesis_write_slot_witness()

    # A new property which *also* returns False is not the original
    # deny-only implementation. Unlike a True getter, this was previously
    # accepted because the post-COMMIT baseline was sampled too late.
    monkeypatch.setattr(
        slots.WriteSlotReservationReceipt, field, property(lambda _: False),
    )
    with pytest.raises(slots.WriteSlotLedgerRejected, match="receipt epoch"):
        ledger.reserve_many((_claim(),), retained=retained)

    # Rejection is after COMMIT. The same local occurrence remains reserved.
    with sqlite3.connect(ledger._path) as conn:
        assert conn.execute("SELECT COUNT(*) FROM synthetic_write_slots").fetchone() == (1,)
    with pytest.raises(slots.WriteSlotLedgerRejected, match="stale"):
        ledger.reserve_many((_claim(),), retained=retained)


def test_intact_original_denials_still_allow_inert_reservation(tmp_path):
    ledger = slots.DisconnectedWriteSlotLedger(tmp_path / "write-slots.sqlite", create=True)
    receipt = ledger.reserve_many(
        (_claim(),), retained=slots.genesis_write_slot_witness(),
    )
    assert type(receipt) is slots.WriteSlotReservationReceipt
    for name in slots._RECEIPT_DENIALS:
        assert getattr(receipt, name) is False
    assert receipt.witness.count == 1
