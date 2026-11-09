"""Disconnected WRITE slot hash/schema/parser custody before private input access.

All SQLite data are synthetic and disposable. Even a durable slot reservation
does not authorize real tools, approve users, or prove exactly-once effects.
"""

from __future__ import annotations

import re

import pytest

from ark.agency import disconnected_write_slot_ledger as slots

PLAN = "plan_" + "a" * 64
STEP = "step_" + "1" * 16
REQUEST = "b" * 64
_MUTATIONS = (
    ("_DOMAIN", b"unreviewed-write-slot-domain\\0"),
    ("_DDL", "CREATE TABLE unreviewed(id INTEGER)"),
    ("_PLAN", re.compile(r"plan_.*\\Z")),
    ("_STEP", re.compile(r"step_.*\\Z")),
    ("_SLOT", re.compile(r"slot_.*\\Z")),
    ("_SHA", re.compile(r".*\\Z")),
)


@pytest.mark.parametrize(("name", "replacement"), _MUTATIONS)
@pytest.mark.parametrize("operation", ("derive", "genesis", "initialize", "inspect", "reserve"))
def test_rebound_slot_protocol_refused_before_claim_or_storage(
    tmp_path, monkeypatch, operation, name, replacement,
):
    path = tmp_path / "existing.sqlite"
    db = slots.DisconnectedWriteSlotLedger(path, create=True)
    retained = slots.genesis_write_slot_witness()
    slot = slots.derive_disconnected_write_slot_id(PLAN, STEP, REQUEST)
    claim = slots.DetachedWriteSlotClaim(slot, PLAN, STEP, REQUEST)
    fresh = tmp_path / "must_not_create.sqlite"
    monkeypatch.setattr(slots, name, replacement)
    with pytest.raises(
        slots.WriteSlotLedgerRejected,
        match="reservation constructor or authority changed",
    ):
        if operation == "derive":
            slots.derive_disconnected_write_slot_id(PLAN, STEP, REQUEST)
        elif operation == "genesis":
            slots.genesis_write_slot_witness()
        elif operation == "initialize":
            slots.DisconnectedWriteSlotLedger(fresh, create=True)
        elif operation == "inspect":
            db.inspect(retained=retained)
        else:
            db.reserve_many((claim,), retained=retained)
    assert not fresh.exists()
    monkeypatch.undo()
    assert db.inspect(retained=retained) == retained


@pytest.mark.parametrize("dependency", ("sha256", "dumps"))
def test_digest_callback_rejected_before_private_claim_is_serialized(
    tmp_path, monkeypatch, dependency,
):
    db = slots.DisconnectedWriteSlotLedger(tmp_path / "slot.sqlite", create=True)
    retained = slots.genesis_write_slot_witness()
    claim = slots.DetachedWriteSlotClaim(
        slots.derive_disconnected_write_slot_id(PLAN, STEP, REQUEST),
        PLAN, STEP, REQUEST,
    )
    callback_calls = []

    def poison(*args, **kwargs):
        callback_calls.append((args, kwargs))
        raise AssertionError("private WRITE identifiers must not be passed here")

    if dependency == "sha256":
        monkeypatch.setattr(slots.hashlib, "sha256", poison)
    else:
        monkeypatch.setattr(slots.json, "dumps", poison)
    with pytest.raises(
        slots.WriteSlotLedgerRejected,
        match="reservation constructor or authority changed",
    ):
        db.reserve_many((claim,), retained=retained)
    assert callback_calls == []
    monkeypatch.undo()
    assert db.inspect(retained=retained) == retained


def test_equal_value_domain_replacement_is_not_accepted(monkeypatch):
    same_bytes = bytes(bytearray(slots._DOMAIN))
    assert same_bytes == slots._DOMAIN and same_bytes is not slots._DOMAIN
    monkeypatch.setattr(slots, "_DOMAIN", same_bytes)
    with pytest.raises(
        slots.WriteSlotLedgerRejected,
        match="reservation constructor or authority changed",
    ):
        slots.derive_disconnected_write_slot_id(PLAN, STEP, REQUEST)


def test_original_slot_contract_returns_only_denial_receipt(tmp_path):
    db = slots.DisconnectedWriteSlotLedger(tmp_path / "slot.sqlite", create=True)
    initial = slots.genesis_write_slot_witness()
    claim = slots.DetachedWriteSlotClaim(
        slots.derive_disconnected_write_slot_id(PLAN, STEP, REQUEST),
        PLAN, STEP, REQUEST,
    )
    saved = db.reserve_many((claim,), retained=initial)
    assert saved.added_count == 1
    assert saved.dispatch_authorized is False
    assert saved.automatic_replay_authorized is False
    assert saved.exact_once_external_effect_proven is False
    assert saved.trusted_clock_verified is False
    assert saved.owner_or_consent_verified is False
    assert db.inspect(retained=saved.witness) == saved.witness
