"""The synthetic preaction schema oracle releases every temporary SQLite handle.

Fixtures are in-memory and inert: a matching DDL is not independent custody,
human permission, actual execution or proof of any external effect.
"""

from __future__ import annotations

import sqlite3
from contextlib import closing

import pytest

import ark.agency.disconnected_atomic_preaction_ledger as atomic


def _fixture(ddl: str) -> sqlite3.Connection:
    conn = sqlite3.connect(":memory:")
    conn.execute(ddl)
    conn.execute(atomic._AUDITS)
    conn.execute("PRAGMA user_version=1")
    return conn


def _record_oracle(monkeypatch):
    captured: list[sqlite3.Connection] = []
    original = atomic.closing

    def tracked(connection):
        captured.append(connection)
        return original(connection)

    monkeypatch.setattr(atomic, "closing", tracked)
    return captured


def _assert_closed(captured: list[sqlite3.Connection]) -> None:
    assert len(captured) == 1
    with pytest.raises(sqlite3.ProgrammingError, match="closed"):
        captured[0].execute("SELECT 1")


def test_atomic_oracle_closes_after_valid_schema(monkeypatch) -> None:
    with closing(_fixture(atomic._INTENTS)) as conn:
        captured = _record_oracle(monkeypatch)
        atomic._schema(conn)
        _assert_closed(captured)


def test_atomic_oracle_closes_after_same_count_schema_rejection(
    monkeypatch,
) -> None:
    changed = atomic._INTENTS.replace(
        "request_sha256 TEXT NOT NULL", "request_sha256 TEXT",
    )
    with closing(_fixture(changed)) as conn:
        captured = _record_oracle(monkeypatch)
        with pytest.raises(
            atomic.AtomicPreactionRejected, match="pre-action schema changed",
        ):
            atomic._schema(conn)
        _assert_closed(captured)


def test_atomic_oracle_closes_when_catalog_read_raises(monkeypatch) -> None:
    class FailedCatalog:
        def __init__(self, connection):
            self.connection = connection

        def execute(self, query, *args):
            if query.startswith("SELECT type,name,tbl_name,sql"):
                raise RuntimeError("injected schema comparison fault")
            return self.connection.execute(query, *args)

    with closing(_fixture(atomic._INTENTS)) as conn:
        captured = _record_oracle(monkeypatch)
        with pytest.raises(
            RuntimeError, match="injected schema comparison fault",
        ):
            atomic._schema(FailedCatalog(conn))
        _assert_closed(captured)
