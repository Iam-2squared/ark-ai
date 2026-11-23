"""Synthetic Personal Context replay ledger restarts without write intent.

A locally retained replay tip is linkable metadata, not consent or disclosure.
"""

from __future__ import annotations

import sqlite3

import pytest

from ark import personal_context_replay_ledger as context


def test_context_replay_existing_open_is_sqlite_read_only(tmp_path):
    path = tmp_path / "context.sqlite"
    context.DisconnectedContextReplayLedger(path, create=True)
    reopened = context.DisconnectedContextReplayLedger(path)
    assert reopened.witness() == context.genesis_offline_context_replay_witness()

    # Exercise the exact production read-only open without replacing the
    # import-original SQLite factory that the replay protocol now pins.
    connection = reopened._open(read_only=True)
    try:
        with pytest.raises(sqlite3.OperationalError, match="readonly"):
            connection.execute("CREATE TABLE forbidden(value TEXT)")
    finally:
        connection.close()

    assert reopened.witness().independent_custody_proven is False


def test_context_replay_existing_open_coexists_with_reserved_writer(tmp_path):
    path = tmp_path / "context.sqlite"
    context.DisconnectedContextReplayLedger(path, create=True)
    with sqlite3.connect(path, timeout=0.05, isolation_level=None) as writer:
        writer.execute("BEGIN IMMEDIATE")
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
