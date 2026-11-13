"""Synthetic WRITE slot bounded hydration and SQLite admission tests."""

from __future__ import annotations

import sqlite3
from contextlib import closing

import pytest

from ark.agency import disconnected_write_slot_ledger as slots


def _claim():
    plan = "plan_" + "1" * 64
    step = "step_" + "2" * 16
    request = "3" * 64
    return slots.DetachedWriteSlotClaim(
        slots.derive_disconnected_write_slot_id(plan, step, request),
        plan, step, request,
    )


@pytest.mark.parametrize("mutation", ("module", "connect", "max_rows", "max_batch"))
@pytest.mark.parametrize("operation", ("create", "reopen"))
def test_write_slot_rejects_replaced_storage_contract_before_sqlite(
    tmp_path, monkeypatch: pytest.MonkeyPatch, mutation: str, operation: str,
) -> None:
    path = tmp_path / "slots.db"
    if operation == "reopen":
        slots.DisconnectedWriteSlotLedger(path, create=True)
    called = []

    def forbidden_connect(*args, **kwargs):
        called.append(True)
        raise AssertionError("hostile connector reached")

    with monkeypatch.context() as patch:
        if mutation == "module":
            patch.setattr(slots, "sqlite3", object())
        elif mutation == "connect":
            patch.setattr(sqlite3, "connect", forbidden_connect)
        elif mutation == "max_rows":
            patch.setattr(slots, "_MAX_ROWS", 1000)
        else:
            patch.setattr(slots, "_MAX_BATCH", True)
        with pytest.raises(
            slots.WriteSlotLedgerRejected,
            match="reservation constructor or authority changed",
        ):
            slots.DisconnectedWriteSlotLedger(
                path, create=operation == "create",
            )
    assert not called
    if operation == "create":
        assert not path.exists()
    else:
        reopened = slots.DisconnectedWriteSlotLedger(path)
        assert reopened.inspect(retained=slots.genesis_write_slot_witness()).count == 0


@pytest.mark.parametrize(("field", "corrupt"), (
    ("slot_id", "slot_" + "a" * 100000),
    ("plan_id", "plan_" + "a" * 100000),
    ("step_id", "step_" + "a" * 100000),
    ("request_sha256", sqlite3.Binary(b"a" * 64)),
    ("chain_sha256", sqlite3.Binary(b"a" * 64)),
))
def test_write_slot_rejects_oversized_or_binary_storage_before_hydration(
    tmp_path, field, corrupt,
):
    path = tmp_path / "slots.db"
    ledger = slots.DisconnectedWriteSlotLedger(path, create=True)
    receipt = ledger.reserve_many(
        (_claim(),), retained=slots.genesis_write_slot_witness(),
    )
    with closing(sqlite3.connect(path)) as conn, conn:
        conn.execute(f"UPDATE synthetic_write_slots SET {field}=? WHERE seq=1", (corrupt,))
    with pytest.raises(
        slots.WriteSlotLedgerRejected, match="invalid persisted reservation row",
    ):
        ledger.inspect(retained=receipt.witness)
    assert receipt.dispatch_authorized is False
    assert receipt.automatic_replay_authorized is False


@pytest.mark.parametrize(("plan", "step", "request"), (
    ("plan_" + "1" * 100000, "step_" + "2" * 16, "a" * 64),
    ("plan_" + "1" * 64, "step_" + "2" * 100000, "a" * 64),
    ("plan_" + "1" * 64, "step_" + "2" * 16, "a" * 100000),
))
def test_write_slot_rejects_oversized_claim_before_digest(plan, step, request):
    with pytest.raises(slots.WriteSlotLedgerRejected, match="invalid exact WRITE"):
        slots.derive_disconnected_write_slot_id(plan, step, request)


def test_write_slot_still_restarts_inertly_with_exact_witness(tmp_path):
    path = tmp_path / "slots.db"
    ledger = slots.DisconnectedWriteSlotLedger(path, create=True)
    receipt = ledger.reserve_many(
        (_claim(),), retained=slots.genesis_write_slot_witness(),
    )
    restarted = slots.DisconnectedWriteSlotLedger(path)
    assert restarted.inspect(retained=receipt.witness) == receipt.witness
    assert receipt.dispatch_authorized is False
    assert receipt.exact_once_external_effect_proven is False
