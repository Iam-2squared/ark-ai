"""A retained WRITE-slot witness must keep its original inert property.

Synthetic SQLite reservations only. Neither a matching witness nor a false
authority getter is consent, a tool permission, or exactly-once external effect.
"""

import sqlite3

import pytest

from ark.agency import disconnected_write_slot_ledger as slots


def _claim():
    plan, step, request = "plan_" + "a" * 64, "step_" + "b" * 16, "c" * 64
    return slots.DetachedWriteSlotClaim(
        slots.derive_disconnected_write_slot_id(plan, step, request),
        plan, step, request,
    )


@pytest.mark.parametrize("action", ("inspect", "reserve"))
@pytest.mark.parametrize("return_value", (False, True))
def test_foreign_witness_authority_getter_never_runs(
    tmp_path, monkeypatch, action, return_value,
):
    db = slots.DisconnectedWriteSlotLedger(tmp_path / "slots.sqlite", create=True)
    retained = slots.genesis_write_slot_witness()
    called = []

    def forged(_self):
        called.append("getter executed")
        return return_value

    with monkeypatch.context() as patch:
        patch.setattr(
            slots.WriteSlotLedgerWitness,
            "independently_authenticated", property(forged),
        )
        with pytest.raises(slots.WriteSlotLedgerRejected, match="invalid retained witness"):
            if action == "inspect":
                db.inspect(retained=retained)
            else:
                db.reserve_many((_claim(),), retained=retained)
    assert called == []
    assert db.inspect(retained=retained) == retained


def test_late_false_getter_after_sqlite_snapshot_cannot_run(
    tmp_path, monkeypatch,
):
    db = slots.DisconnectedWriteSlotLedger(tmp_path / "slots.sqlite", create=True)
    retained = slots.genesis_write_slot_witness()
    original = slots._inspect
    calls = []

    def forged(_self):
        calls.append("unexpected")
        return False

    with monkeypatch.context() as patch:
        def corrupt_after_read(conn):
            result = original(conn)
            patch.setattr(
                slots.WriteSlotLedgerWitness,
                "independently_authenticated", property(forged),
            )
            return result

        patch.setattr(slots, "_inspect", corrupt_after_read)
        with pytest.raises(slots.WriteSlotLedgerRejected, match="invalid retained witness"):
            db.reserve_many((_claim(),), retained=retained)
    assert calls == []
    with sqlite3.connect(db._path) as conn:
        assert conn.execute(
            "SELECT COUNT(*) FROM synthetic_write_slots"
        ).fetchone() == (0,)
    assert db.inspect(retained=retained) == retained


def test_original_witness_still_reserves_inert_occurrence(tmp_path):
    db = slots.DisconnectedWriteSlotLedger(tmp_path / "slots.sqlite", create=True)
    receipt = db.reserve_many(
        (_claim(),), retained=slots.genesis_write_slot_witness(),
    )
    assert receipt.added_count == 1
    assert receipt.dispatch_authorized is False
    assert receipt.automatic_replay_authorized is False
    assert receipt.witness.independently_authenticated is False
    assert db.inspect(retained=receipt.witness) == receipt.witness
