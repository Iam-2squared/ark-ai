"""Detached WRITE reservations must reject fabricated custody/authority.

No action is dispatched. Failed reservations must leave the SQLite tip intact.
"""

from __future__ import annotations

import pytest

from ark.agency import disconnected_write_slot_ledger as slots


def _claim():
    plan = "plan_" + "a" * 64
    step = "step_" + "b" * 16
    request = "c" * 64
    return slots.DetachedWriteSlotClaim(
        slots.derive_disconnected_write_slot_id(plan, step, request),
        plan, step, request,
    )


def test_reserve_rejects_authority_spoof_before_insert(tmp_path, monkeypatch):
    path = tmp_path / "slots.sqlite"
    ledger = slots.DisconnectedWriteSlotLedger(path, create=True)
    retained = slots.genesis_write_slot_witness()
    original = slots._inspect

    with monkeypatch.context() as patch:
        def spoof_after_sqlite_read(conn):
            observed = original(conn)
            patch.setattr(
                slots.WriteSlotLedgerWitness,
                "independently_authenticated",
                property(lambda self: True),
            )
            return observed

        patch.setattr(slots, "_inspect", spoof_after_sqlite_read)
        with pytest.raises(slots.WriteSlotLedgerRejected, match="invalid retained witness"):
            ledger.reserve_many((_claim(),), retained=retained)

    assert ledger.inspect(retained=retained) == retained


def test_inspect_rejects_equal_value_nonexact_sqlite_witness(
    tmp_path, monkeypatch,
):
    path = tmp_path / "slots.sqlite"
    ledger = slots.DisconnectedWriteSlotLedger(path, create=True)
    retained = slots.genesis_write_slot_witness()

    class StringSubtype(str):
        pass

    altered = slots.WriteSlotLedgerWitness(
        retained.count, StringSubtype(retained.chain_sha256),
    )
    assert altered == retained
    assert type(altered.chain_sha256) is not str

    with monkeypatch.context() as patch:
        patch.setattr(slots, "_inspect", lambda conn: altered)
        with pytest.raises(slots.WriteSlotLedgerRejected, match="invalid retained witness"):
            ledger.inspect(retained=retained)

    assert ledger.inspect(retained=retained) == retained
