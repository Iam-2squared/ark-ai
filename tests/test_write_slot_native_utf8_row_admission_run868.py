"""UTF-8 byte-width admission of disconnected WRITE reservations.

No real WRITE, token grant, approval issuer, trusted clock or external effect.
Only isolated synthetic SQLite and local SQL trace callbacks are used.
"""

from __future__ import annotations

import sqlite3

import pytest

from ark.agency.disconnected_write_slot_ledger import (
    DetachedWriteSlotClaim,
    DisconnectedWriteSlotLedger,
    WriteSlotLedgerRejected,
    _inspect,
    derive_disconnected_write_slot_id,
    genesis_write_slot_witness,
)


def _seed(tmp_path):
    db = DisconnectedWriteSlotLedger(tmp_path / "reservations.sqlite", create=True)
    plan = "plan_" + "0" * 64
    step = "step_" + "0" * 16
    request = "1" * 64
    claim = DetachedWriteSlotClaim(
        derive_disconnected_write_slot_id(plan, step, request),
        plan, step, request,
    )
    db.reserve_many((claim,), retained=genesis_write_slot_witness())
    return db


@pytest.mark.parametrize(
    ("column", "forged"),
    (
        ("slot_id", "slot_" + "é" * 64),
        ("plan_id", "plan_" + "é" * 64),
        ("step_id", "step_" + "é" * 16),
        ("request_sha256", "é" * 64),
        ("chain_sha256", "é" * 64),
    ),
)
def test_utf8_byte_length_mismatch_refused_before_reservation_row_hydration(
    tmp_path, column, forged,
):
    db = _seed(tmp_path)
    with sqlite3.connect(db._path) as conn:
        assert conn.execute(
            f"UPDATE synthetic_write_slots SET {column}=? WHERE seq=1",
            (forged,),
        ).rowcount == 1

    executed = []
    with sqlite3.connect(db._path) as conn:
        conn.set_trace_callback(executed.append)
        conn.execute("BEGIN")
        with pytest.raises(WriteSlotLedgerRejected, match="invalid persisted reservation row"):
            _inspect(conn)
    assert any(
        "length(CAST(" + column + " AS BLOB))" in sql
        for sql in executed
    )
    assert not any(
        "SELECT seq,slot_id,plan_id,step_id" in sql
        for sql in executed
    )


def test_ordinary_ascii_reservation_survives_byte_width_preflight(tmp_path):
    db = _seed(tmp_path)
    with sqlite3.connect(db._path) as conn:
        conn.execute("BEGIN")
        observed = _inspect(conn)
    assert observed.count == 1
    assert observed == db.inspect(retained=observed)
    assert observed.independently_authenticated is False
