"""Constructor/denial custody for durable *synthetic* WRITE slots only.

These tests do not authorize an external action, guarantee exactly-once external
effects, or imply that a locally retained witness is authenticated.
"""

import sqlite3

import pytest

from ark.agency import disconnected_write_slot_ledger as module


def _case(tmp_path):
    db = module.DisconnectedWriteSlotLedger(tmp_path / "slots.sqlite", create=True)
    retained = module.genesis_write_slot_witness()
    plan = "plan_" + "1" * 64
    step = "step_" + "2" * 16
    request = "3" * 64
    claim = module.DetachedWriteSlotClaim(
        module.derive_disconnected_write_slot_id(plan, step, request),
        plan, step, request,
    )
    return db, retained, claim


@pytest.mark.parametrize(
    "target",
    ("witness_init", "receipt_init", "receipt_symbol"),
)
def test_preinstalled_executable_result_definition_never_reaches_write(
    tmp_path, monkeypatch, target,
):
    db, retained, claim = _case(tmp_path)
    executed = []

    def hostile(*args, **kwargs):
        executed.append((args, kwargs))
        raise AssertionError("untrusted constructor or property was executed")

    with monkeypatch.context() as patch:
        if target == "witness_init":
            patch.setattr(module.WriteSlotLedgerWitness, "__init__", hostile)
        elif target == "receipt_init":
            patch.setattr(module.WriteSlotReservationReceipt, "__init__", hostile)
        elif target == "receipt_symbol":
            patch.setattr(module, "WriteSlotReservationReceipt", hostile)
        with pytest.raises(
            module.WriteSlotLedgerRejected, match="constructor or authority changed",
        ):
            db.reserve_many((claim,), retained=retained)

    assert executed == []
    with sqlite3.connect(tmp_path / "slots.sqlite") as connection:
        assert connection.execute(
            "SELECT COUNT(*) FROM synthetic_write_slots"
        ).fetchone() == (0,)
    assert db.inspect(retained=retained) == retained


def test_row_digest_callback_constructor_replacement_rolls_back(tmp_path, monkeypatch):
    db, retained, claim = _case(tmp_path)
    executed = []
    triggered = []
    original_hash = module._hash

    def hostile(*args, **kwargs):
        executed.append((args, kwargs))
        raise AssertionError("untrusted witness constructor executed")

    with monkeypatch.context() as patch:
        # The scoped fixture restores a callback-injected class after denial.
        def hooked(fields):
            digest = original_hash(fields)
            if fields[0] == "row":
                triggered.append(fields[0])
                patch.setattr(module.WriteSlotLedgerWitness, "__init__", hostile)
            return digest
        patch.setattr(module, "_hash", hooked)
        with pytest.raises(
            module.WriteSlotLedgerRejected, match="constructor or authority changed",
        ):
            db.reserve_many((claim,), retained=retained)

    assert triggered == ["row"]
    assert executed == []
    assert db.inspect(retained=retained) == retained


def test_original_constructor_returns_non_authorizing_durable_receipt(tmp_path):
    db, retained, claim = _case(tmp_path)
    receipt = db.reserve_many((claim,), retained=retained)
    assert receipt.added_count == 1
    assert type(receipt) is module.WriteSlotReservationReceipt
    assert receipt.dispatch_authorized is False
    assert receipt.automatic_replay_authorized is False
    assert receipt.exact_once_external_effect_proven is False
    assert db.inspect(retained=receipt.witness) == receipt.witness
