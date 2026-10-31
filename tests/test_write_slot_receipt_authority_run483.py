"""Durable synthetic WRITE reservations must never promote a receipt to authority."""

from __future__ import annotations

import sqlite3

import pytest

import ark.agency.disconnected_write_slot_ledger as slots


def _claim():
    plan = "plan_" + "a" * 64
    step = "step_" + "b" * 16
    request = "c" * 64
    return slots.DetachedWriteSlotClaim(
        slots.derive_disconnected_write_slot_id(plan, step, request),
        plan, step, request,
    )


def _db(tmp_path):
    return slots.DisconnectedWriteSlotLedger(tmp_path / "writes.db", create=True)


@pytest.mark.parametrize("authority", [
    "dispatch_authorized",
    "automatic_replay_authorized",
    "exact_once_external_effect_proven",
    "trusted_clock_verified",
    "owner_or_consent_verified",
])
def test_postcommit_receipt_authority_forgery_rejected_without_retry(
    tmp_path, monkeypatch, authority,
):
    ledger = _db(tmp_path)
    retained = slots.genesis_write_slot_witness()
    monkeypatch.setattr(
        slots.WriteSlotReservationReceipt, authority,
        property(lambda self: True),
    )
    with pytest.raises(slots.WriteSlotLedgerRejected, match="post-commit"):
        ledger.reserve_many((_claim(),), retained=retained)
    with sqlite3.connect(ledger._path) as conn:
        assert conn.execute("SELECT COUNT(*) FROM synthetic_write_slots").fetchone() == (1,)
    with pytest.raises(slots.WriteSlotLedgerRejected, match="stale"):
        ledger.inspect(retained=retained)


def test_forged_constructor_type_rejected_after_commit(tmp_path, monkeypatch):
    ledger = _db(tmp_path)
    retained = slots.genesis_write_slot_witness()
    original = slots.WriteSlotReservationReceipt

    class ForgedReceipt:
        def __init__(self, count, witness):
            self.added_count = count
            self.witness = witness
            self.dispatch_authorized = False
            self.automatic_replay_authorized = False
            self.exact_once_external_effect_proven = False
            self.trusted_clock_verified = False
            self.owner_or_consent_verified = False

    monkeypatch.setattr(slots, "WriteSlotReservationReceipt", ForgedReceipt)
    with pytest.raises(slots.WriteSlotLedgerRejected, match="post-commit"):
        ledger.reserve_many((_claim(),), retained=retained)
    monkeypatch.setattr(slots, "WriteSlotReservationReceipt", original)
    with sqlite3.connect(ledger._path) as conn:
        assert conn.execute("SELECT COUNT(*) FROM synthetic_write_slots").fetchone() == (1,)


def test_claimed_independent_witness_authority_is_rejected_before_write(tmp_path, monkeypatch):
    ledger = _db(tmp_path)
    monkeypatch.setattr(
        slots.WriteSlotLedgerWitness, "independently_authenticated",
        property(lambda self: True),
    )
    with pytest.raises(slots.WriteSlotLedgerRejected, match="witness"):
        ledger.reserve_many(
            (_claim(),), retained=slots.genesis_write_slot_witness(),
        )
    with sqlite3.connect(ledger._path) as conn:
        assert conn.execute("SELECT COUNT(*) FROM synthetic_write_slots").fetchone() == (0,)


def test_normal_receipt_remains_denial_only(tmp_path):
    ledger = _db(tmp_path)
    result = ledger.reserve_many(
        (_claim(),), retained=slots.genesis_write_slot_witness(),
    )
    assert result.added_count == 1
    assert result.witness.count == 1
    assert result.dispatch_authorized is False
    assert result.automatic_replay_authorized is False
    assert result.exact_once_external_effect_proven is False
    assert result.trusted_clock_verified is False
    assert result.owner_or_consent_verified is False
    assert result.witness.independently_authenticated is False
