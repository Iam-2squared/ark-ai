"""Durable Planner WRITE slot restart is pure observation, not permission."""

from __future__ import annotations

import sqlite3

from ark.agency import disconnected_write_slot_ledger as slots


def test_existing_write_slot_ledger_uses_read_only_sqlite_transaction(
    tmp_path, monkeypatch,
):
    path = tmp_path / "slots.sqlite"
    slots.DisconnectedWriteSlotLedger(path, create=True)
    original_connect = sqlite3.connect
    opens = []
    statements = []

    def observed_connect(database, *args, **kwargs):
        conn = original_connect(database, *args, **kwargs)
        if database != ":memory:":
            opens.append(database)
            conn.set_trace_callback(statements.append)
        return conn

    monkeypatch.setattr(slots.sqlite3, "connect", observed_connect)
    restarted = slots.DisconnectedWriteSlotLedger(path)
    genesis = slots.genesis_write_slot_witness()
    assert restarted.inspect(retained=genesis) == genesis
    assert opens
    assert all(name.endswith("?mode=ro") for name in opens)
    normalized = [statement.strip().upper() for statement in statements]
    assert "BEGIN" in normalized
    assert not any(
        statement.startswith(("BEGIN IMMEDIATE", "CREATE ", "INSERT ", "UPDATE ", "DELETE "))
        for statement in normalized
    )
    assert genesis.independently_authenticated is False


def test_existing_write_slot_restart_can_read_under_reserved_writer(
    tmp_path, monkeypatch,
):
    path = tmp_path / "slots.sqlite"
    slots.DisconnectedWriteSlotLedger(path, create=True)
    original_connect = sqlite3.connect
    with original_connect(path, timeout=0.05, isolation_level=None) as writer:
        writer.execute("BEGIN IMMEDIATE")

        def fast_connect(database, *args, **kwargs):
            if database != ":memory:":
                kwargs["timeout"] = 0.05
            return original_connect(database, *args, **kwargs)

        monkeypatch.setattr(slots.sqlite3, "connect", fast_connect)
        try:
            restarted = slots.DisconnectedWriteSlotLedger(path)
            genesis = slots.genesis_write_slot_witness()
            assert restarted.inspect(retained=genesis) == genesis
        finally:
            writer.rollback()
    assert path.exists()


def test_write_slot_restart_must_not_create_missing_storage(tmp_path):
    path = tmp_path / "missing.sqlite"
    try:
        slots.DisconnectedWriteSlotLedger(path)
    except slots.WriteSlotLedgerRejected as exc:
        assert "missing durable reservation ledger" in str(exc)
    else:
        raise AssertionError("missing write reservations must not be re-created")
    assert not path.exists()
