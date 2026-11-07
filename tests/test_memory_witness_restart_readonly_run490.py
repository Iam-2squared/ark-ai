"""Existing disconnected Memory witness ledger inspection takes no write lock.

The witness is merely caller-retained local metadata, not authenticated custody,
independent provenance, privacy consent, or permission to dispatch.
"""

from __future__ import annotations

import sqlite3

from ark.memory import disconnected_witness_ledger as witness


def test_existing_memory_ledger_open_is_only_read_sqlite_transaction(
    tmp_path, monkeypatch,
):
    path = tmp_path / "witness.sqlite"
    witness.DisconnectedMemoryWitnessLedger(path, create=True)
    original_connect = sqlite3.connect
    opens = []
    statements = []

    def capture(database, *args, **kwargs):
        conn = original_connect(database, *args, **kwargs)
        if database != ":memory:":
            opens.append(database)
            conn.set_trace_callback(statements.append)
        return conn

    monkeypatch.setattr(witness.sqlite3, "connect", capture)
    reopened = witness.DisconnectedMemoryWitnessLedger(path)
    retained = witness.genesis_memory_ledger_witness()
    assert reopened.inspect(retained=retained) == retained
    assert opens
    assert all(uri.endswith("?mode=ro") for uri in opens)
    normalized = [sql.strip().upper() for sql in statements]
    assert "BEGIN" in normalized
    assert not any(
        sql.startswith(("BEGIN IMMEDIATE", "CREATE ", "INSERT ", "UPDATE ", "DELETE "))
        for sql in normalized
    )
    assert retained.custody_authenticated is False
    assert retained.independent_writer_proven is False
    assert retained.memory_disclosure_authorized is False


def test_existing_memory_ledger_open_coexists_with_reserved_writer(
    tmp_path, monkeypatch,
):
    path = tmp_path / "witness.sqlite"
    witness.DisconnectedMemoryWitnessLedger(path, create=True)
    original_connect = sqlite3.connect
    with original_connect(path, isolation_level=None, timeout=0.05) as writer:
        writer.execute("BEGIN IMMEDIATE")

        def fast_connect(database, *args, **kwargs):
            if database != ":memory:":
                kwargs["timeout"] = 0.05
            return original_connect(database, *args, **kwargs)

        monkeypatch.setattr(witness.sqlite3, "connect", fast_connect)
        try:
            reopened = witness.DisconnectedMemoryWitnessLedger(path)
            retained = witness.genesis_memory_ledger_witness()
            assert reopened.inspect(retained=retained) == retained
        finally:
            writer.rollback()
    assert path.exists()


def test_existing_memory_ledger_does_not_recreate_missing_storage(tmp_path):
    path = tmp_path / "missing.sqlite"
    try:
        witness.DisconnectedMemoryWitnessLedger(path)
    except witness.MemoryWitnessLedgerRejected as exc:
        assert "missing retained ledger" in str(exc)
    else:
        raise AssertionError("read-only restart accepted missing ledger")
    assert not path.exists()
