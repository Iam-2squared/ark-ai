"""Bound every SQLite catalog name before hydrating detached schema metadata.

Only a disposable in-memory SQLite catalog is modified. No user database,
persistent schema, real tool, authorization, or external operation is touched.
"""

from __future__ import annotations

import sqlite3
from contextlib import closing

import pytest

from ark import disconnected_sqlite_schema_probe as probe


@pytest.mark.parametrize("column", ("name", "tbl_name"))
def test_corrupted_large_catalog_name_rejected_before_python_rows(column):
    with closing(sqlite3.connect(":memory:")) as conn:
        conn.execute("CREATE TABLE fixture(id INTEGER)")
        # SQLite's isolated writable_schema hook creates a synthetic catalog
        # inconsistency not possible through a normal CREATE TABLE statement:
        # a huge name while the SQL statement itself stays tiny.
        conn.execute("PRAGMA writable_schema=ON")
        conn.execute(
            f"UPDATE sqlite_master SET {column}=? WHERE name='fixture'",
            ("s" * 66_000,),
        )
        conn.execute("PRAGMA writable_schema=OFF")
        # The fault-injection UPDATE starts an implicit write transaction.
        # Commit the synthetic corrupted catalog first: the production probe
        # intentionally refuses non-idle connections before inspecting data.
        assert conn.in_transaction
        conn.commit()
        assert not conn.in_transaction
        conn.execute("PRAGMA query_only=ON")
        statements = []
        conn.set_trace_callback(statements.append)
        with pytest.raises(
            probe.SQLiteSchemaProbeRejected, match="preflight exceeds byte budget",
        ):
            probe.capture_disconnected_sqlite_schema(conn)
        assert not conn.in_transaction
        assert any("SUM(length(CAST(sql AS BLOB)))" in sql for sql in statements)
        assert not any(
            "SELECT type,name,tbl_name,sql FROM sqlite_master" in sql
            for sql in statements
        )


def test_bounded_nonempty_catalog_remains_inert_and_repeatable():
    with closing(sqlite3.connect(":memory:")) as conn:
        conn.execute("CREATE TABLE fixture(id INTEGER PRIMARY KEY)")
        conn.execute("PRAGMA query_only=ON")
        baseline = probe.capture_disconnected_sqlite_schema(conn)
        assert probe.review_disconnected_sqlite_schema(conn, baseline) == baseline
        assert baseline.object_count >= 1
        assert baseline.source_authenticated is False
        assert baseline.application_data_disclosure_authorized is False
        assert baseline.cross_store_atomicity_proven is False
