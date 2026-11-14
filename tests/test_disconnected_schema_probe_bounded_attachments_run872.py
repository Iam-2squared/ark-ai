"""Detached SQLite schema capture rejects attached DBs without state changes.

Only memory-backed SQLite fixtures are opened; no application data or real
authorization is surfaced by these synthetic schema seals.
"""

from __future__ import annotations

import sqlite3
from contextlib import closing

import pytest

from ark.disconnected_sqlite_schema_probe import (
    SQLiteSchemaProbeRejected,
    capture_disconnected_sqlite_schema,
    review_disconnected_sqlite_schema,
)


def _main() -> sqlite3.Connection:
    conn = sqlite3.connect(":memory:")
    conn.execute("CREATE TABLE fixture (id INTEGER PRIMARY KEY)")
    conn.execute("PRAGMA query_only=ON")
    return conn


@pytest.mark.parametrize("attachment_count", (1, 2, 3))
def test_reject_attached_dbs_and_recover_without_any_implicit_detach(
    attachment_count: int,
) -> None:
    with closing(_main()) as conn:
        baseline = capture_disconnected_sqlite_schema(conn)
        aliases = [f"synthetic_{index}" for index in range(attachment_count)]
        for name in aliases:
            conn.execute(f"ATTACH DATABASE ':memory:' AS {name}")
        before = conn.execute("PRAGMA database_list").fetchall()
        assert len(before) == attachment_count + 1
        with pytest.raises(SQLiteSchemaProbeRejected, match="single main"):
            capture_disconnected_sqlite_schema(conn)
        with pytest.raises(SQLiteSchemaProbeRejected, match="single main"):
            review_disconnected_sqlite_schema(conn, baseline)
        assert not conn.in_transaction
        assert conn.execute("PRAGMA database_list").fetchall() == before
        assert conn.execute("PRAGMA query_only").fetchone() == (1,)
        for name in reversed(aliases):
            conn.execute(f"DETACH DATABASE {name}")
        assert review_disconnected_sqlite_schema(conn, baseline) == baseline
        assert baseline.application_data_disclosure_authorized is False
