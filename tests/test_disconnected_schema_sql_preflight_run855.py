"""Detached schema-probe SQL admission, bounded before Python DDL hydration.

No real application rows, disclosure, writable SQLite connection, or external
execution. A transaction-local SQL count is not an authenticated seal.
"""

from __future__ import annotations

import sqlite3
from contextlib import closing

import pytest

from ark import disconnected_sqlite_schema_probe as probe


@pytest.mark.parametrize("case", ("too_many_objects", "too_many_ddl_bytes"))
def test_schema_preflight_blocks_python_ddl_scan(
    case: str,
) -> None:
    with closing(sqlite3.connect(":memory:")) as connection:
        if case == "too_many_objects":
            for n in range(129):
                connection.execute(f"CREATE TABLE tab_{n} (id INTEGER)")
        else:
            private_fixture = "a" * 66_000
            connection.execute(
                f"CREATE TABLE long_default (item TEXT DEFAULT '{private_fixture}')"
            )
        connection.execute("PRAGMA query_only=ON")
        seen_sql: list[str] = []
        connection.set_trace_callback(seen_sql.append)
        with pytest.raises(probe.SQLiteSchemaProbeRejected, match="budget"):
            probe.capture_disconnected_sqlite_schema(connection)
        assert not connection.in_transaction
        # SQL admission happened; Python never selected private DDL rows.
        assert any("SUM(length(CAST(sql AS BLOB)))" in sql for sql in seen_sql)
        assert not any("SELECT type,name,tbl_name,sql FROM sqlite_master" in sql
                       for sql in seen_sql)


def test_preflight_query_rebinding_denied_before_database_read(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    with closing(sqlite3.connect(":memory:")) as connection:
        connection.execute("CREATE TABLE sample (id INTEGER)")
        connection.execute("PRAGMA query_only=ON")
        seen_sql: list[str] = []
        connection.set_trace_callback(seen_sql.append)
        monkeypatch.setattr(
            probe, "_PREFLIGHT_QUERY", "SELECT sql FROM sqlite_master"
        )
        with pytest.raises(probe.SQLiteSchemaProbeRejected, match="contract"):
            probe.capture_disconnected_sqlite_schema(connection)
        assert seen_sql == []
        assert not connection.in_transaction


def test_normal_schema_remains_a_deny_only_receipt() -> None:
    with closing(sqlite3.connect(":memory:")) as connection:
        connection.execute("CREATE TABLE sample (id INTEGER, value TEXT)")
        connection.execute("PRAGMA query_only=ON")
        result = probe.capture_disconnected_sqlite_schema(connection)
        assert result.object_count == 1
        assert probe.review_disconnected_sqlite_schema(connection, result) == result
        assert result.source_authenticated is False
        assert result.independent_custody_proven is False
        assert result.application_data_disclosure_authorized is False
        assert result.wal_snapshot_verified is False
