"""Detached WRITE ledger must reject carrier/path swaps across SQLite review.

No test here dispatches a tool, authorizes a WRITE or claims an external effect.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from ark.agency import disconnected_write_slot_ledger as slots


def _rebind_same_path(value: Path) -> Path:
    other = Path(str(value))
    assert other == value and other is not value
    return other


def test_readonly_inspect_rejects_path_rebind_after_sqlite_read(tmp_path, monkeypatch):
    path = tmp_path / "slots.sqlite"
    ledger = slots.DisconnectedWriteSlotLedger(path, create=True)
    retained = slots.genesis_write_slot_witness()
    original = slots._inspect

    def altered_inspect(conn):
        result = original(conn)
        ledger._path = _rebind_same_path(ledger._path)
        return result

    monkeypatch.setattr(slots, "_inspect", altered_inspect)
    with pytest.raises(slots.WriteSlotLedgerRejected, match="custody changed"):
        ledger.inspect(retained=retained)


def test_readonly_inspect_rejects_equal_text_witness_replacement(tmp_path, monkeypatch):
    path = tmp_path / "slots.sqlite"
    ledger = slots.DisconnectedWriteSlotLedger(path, create=True)
    retained = slots.genesis_write_slot_witness()
    original_hash = retained.chain_sha256
    original = slots._inspect

    def altered_inspect(conn):
        result = original(conn)
        replacement = ("0" + original_hash)[1:]
        assert replacement == original_hash and replacement is not original_hash
        object.__setattr__(retained, "chain_sha256", replacement)
        return result

    monkeypatch.setattr(slots, "_inspect", altered_inspect)
    with pytest.raises(slots.WriteSlotLedgerRejected, match="custody changed"):
        ledger.inspect(retained=retained)


def test_reservation_rejects_path_swap_before_insert(tmp_path, monkeypatch):
    path = tmp_path / "slots.sqlite"
    ledger = slots.DisconnectedWriteSlotLedger(path, create=True)
    genesis = slots.genesis_write_slot_witness()
    plan = "plan_" + "a" * 64
    step = "step_" + "b" * 16
    request = "c" * 64
    identity = slots.derive_disconnected_write_slot_id(plan, step, request)
    claim = slots.DetachedWriteSlotClaim(identity, plan, step, request)
    original = slots._inspect

    def altered_inspect(conn):
        result = original(conn)
        ledger._path = _rebind_same_path(ledger._path)
        return result

    monkeypatch.setattr(slots, "_inspect", altered_inspect)
    with pytest.raises(slots.WriteSlotLedgerRejected, match="carriers changed"):
        ledger.reserve_many((claim,), retained=genesis)
    monkeypatch.setattr(slots, "_inspect", original)
    assert slots.DisconnectedWriteSlotLedger(path).inspect(retained=genesis) == genesis
