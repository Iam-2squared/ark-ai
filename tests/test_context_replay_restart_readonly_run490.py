"""Synthetic Personal Context replay ledger restarts without write intent.

A locally retained replay tip is linkable metadata, not consent or disclosure.
"""

from __future__ import annotations

import sqlite3

from ark import personal_context_replay_ledger as context


def test_context_replay_existing_open_is_sqlite_read_only(tmp_path, monkeypatch):
    path = tmp_path / "context.sqlite"
    context.DisconnectedContextReplayLedger(path, create=True)
    original_connect = sqlite3.connect
    opens = []
    statements = []

    def trace_connect(database, *args, **kwargs):
        conn = original_connect(database, *args, **kwargs)
        if database != ":memory:":
            opens.append(database)
            conn.set_trace_callback(statements.append)
        return conn

    monkeypatch.setattr(context.sqlite3, "connect", trace_connect)
    reopened = context.DisconnectedContextReplayLedger(path)
    assert reopened.witness() == context.genesis_offline_context_replay_witness()
    assert opens
    assert all(name.endswith("?mode=ro") for name in opens)
    normalized = [query.strip().upper() for query in statements]
    assert "BEGIN" in normalized
    assert not any(
        query.startswith(("BEGIN IMMEDIATE", "CREATE ", "INSERT ", "UPDATE ", "DELETE "))
        for query in normalized
    )
    assert reopened.witness().independent_custody_proven is False


def test_context_replay_existing_open_coexists_with_reserved_writer(
    tmp_path, monkeypatch,
):
    path = tmp_path / "context.sqlite"
    context.DisconnectedContextReplayLedger(path, create=True)
    original_connect = sqlite3.connect
    with original_connect(path, timeout=0.05, isolation_level=None) as writer:
        writer.execute("BEGIN IMMEDIATE")

        def fast_connect(database, *args, **kwargs):
            if database != ":memory:":
                kwargs["timeout"] = 0.05
            return original_connect(database, *args, **kwargs)

        monkeypatch.setattr(context.sqlite3, "connect", fast_connect)
        try:
            reopened = context.DisconnectedContextReplayLedger(path)
            assert reopened.witness() == context.genesis_offline_context_replay_witness()
        finally:
            writer.rollback()
    assert path.exists()


def test_context_replay_existing_open_refuses_missing_database(tmp_path):
    path = tmp_path / "missing.sqlite"
    try:
        context.DisconnectedContextReplayLedger(path)
    except context.OfflineContextReplayRejected as exc:
        assert "context ledger is missing" in str(exc)
    else:
        raise AssertionError("Personal Context restart recreated missing ledger")
    assert not path.exists()
