"""Durable synthetic WRITE reservation denies executable receipt descriptors.

Only disconnected local SQLite fixtures are exercised. A reservation cannot
authorize tool dispatch, attest an effect, or license automatic replay.
"""

from __future__ import annotations

import subprocess
import sys

import pytest

from ark.agency import disconnected_write_slot_ledger as slots

_SCRIPT = """
import sqlite3
import sys
from pathlib import Path

from ark.agency import disconnected_write_slot_ledger as slots

path = Path(sys.argv[2])
ledger = slots.DisconnectedWriteSlotLedger(path, create=True)
retained = slots.genesis_write_slot_witness()
plan = "plan_" + "1" * 64
step = "step_" + "2" * 16
request = "3" * 64
claim = slots.DetachedWriteSlotClaim(
    slots.derive_disconnected_write_slot_id(plan, step, request),
    plan, step, request,
)
executed = []

def hostile(*args, **kwargs):
    executed.append("untrusted result descriptor executed")
    raise AssertionError("hostile receipt code reached")

kind = sys.argv[1]
if kind == "count":
    slots.WriteSlotReservationReceipt.added_count = property(hostile)
elif kind == "witness":
    slots.WriteSlotReservationReceipt.witness = property(hostile)
elif kind == "lookup":
    slots.WriteSlotReservationReceipt.__getattribute__ = hostile
elif kind == "new":
    slots.WriteSlotReservationReceipt.__new__ = staticmethod(hostile)
else:
    raise AssertionError("unknown fixture")
try:
    ledger.reserve_many((claim,), retained=retained)
except slots.WriteSlotLedgerRejected as exc:
    assert "constructor or authority changed" in str(exc), str(exc)
else:
    raise AssertionError("hostile receipt descriptor was accepted")
assert executed == []
with sqlite3.connect(path) as conn:
    assert conn.execute(
        "SELECT COUNT(*) FROM synthetic_write_slots"
    ).fetchone() == (0,)
"""


@pytest.mark.parametrize("kind", ("count", "witness", "lookup", "new"))
def test_preinstalled_receipt_descriptor_denied_before_sqlite_write(
    tmp_path, kind,
):
    process = subprocess.run(
        [
            sys.executable, "-c", _SCRIPT,
            kind, str(tmp_path / f"{kind}-write.sqlite"),
        ],
        capture_output=True, text=True, check=False, timeout=30,
    )
    assert process.returncode == 0, process.stderr


def test_original_receipt_remains_local_only_and_never_authorizes_replay(tmp_path):
    ledger = slots.DisconnectedWriteSlotLedger(
        tmp_path / "healthy-write.sqlite", create=True,
    )
    old = slots.genesis_write_slot_witness()
    plan = "plan_" + "1" * 64
    step = "step_" + "2" * 16
    request = "3" * 64
    claim = slots.DetachedWriteSlotClaim(
        slots.derive_disconnected_write_slot_id(plan, step, request),
        plan, step, request,
    )
    result = ledger.reserve_many((claim,), retained=old)
    assert result.added_count == 1
    assert result.dispatch_authorized is False
    assert result.automatic_replay_authorized is False
    assert result.exact_once_external_effect_proven is False
    assert ledger.inspect(retained=result.witness) == result.witness
