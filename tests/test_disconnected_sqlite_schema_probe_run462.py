"""Read-only synthetic SQLite metadata checks; no application-row extraction."""

import sqlite3
from contextlib import closing
from dataclasses import FrozenInstanceError, replace

import pytest

from ark.disconnected_sqlite_schema_probe import (
    DisconnectedSQLiteSchemaSeal,
    SQLiteSchemaProbeRejected,
    capture_disconnected_sqlite_schema,
    review_disconnected_sqlite_schema,
)


def _db():
    conn = sqlite3.connect(":memory:")
    conn.execute("CREATE TABLE example (id INTEGER PRIMARY KEY, value TEXT NOT NULL)")
    conn.execute("CREATE INDEX example_value ON example (value)")
    conn.execute("PRAGMA user_version=2")
    conn.execute("PRAGMA query_only=ON")
    return conn


def test_stable_schema_digest_and_no_authorization():
    with closing(_db()) as conn:
        a = capture_disconnected_sqlite_schema(conn)
        assert a == capture_disconnected_sqlite_schema(conn)
        assert a == review_disconnected_sqlite_schema(conn, a)
        assert a.object_count == 2
        assert a.user_version == 2
        assert a.source_authenticated is False
        assert a.independent_custody_proven is False
        assert a.wal_snapshot_verified is False
        assert a.cross_store_atomicity_proven is False
        assert a.application_data_disclosure_authorized is False
        assert len(a.schema_sha256) == 64


def test_application_rows_not_included_in_schema_digest():
    with closing(_db()) as conn:
        first = capture_disconnected_sqlite_schema(conn)
        conn.execute("PRAGMA query_only=OFF")
        conn.execute("INSERT INTO example (value) VALUES ('synthetic private marker')")
        conn.commit()
        conn.execute("PRAGMA query_only=ON")
        assert capture_disconnected_sqlite_schema(conn) == first
        assert "synthetic private marker" not in repr(first)


def test_schema_change_and_user_version_drift_rejected():
    with closing(_db()) as conn:
        baseline = capture_disconnected_sqlite_schema(conn)
        conn.execute("PRAGMA query_only=OFF")
        conn.execute("ALTER TABLE example ADD COLUMN future INTEGER")
        conn.execute("PRAGMA query_only=ON")
        with pytest.raises(SQLiteSchemaProbeRejected, match="differ"):
            review_disconnected_sqlite_schema(conn, baseline)
        again = capture_disconnected_sqlite_schema(conn)
        conn.execute("PRAGMA query_only=OFF")
        conn.execute("PRAGMA user_version=3")
        conn.execute("PRAGMA query_only=ON")
        with pytest.raises(SQLiteSchemaProbeRejected, match="differ"):
            review_disconnected_sqlite_schema(conn, again)


def test_trigger_and_view_are_not_ignored():
    with closing(_db()) as conn:
        baseline = capture_disconnected_sqlite_schema(conn)
        conn.execute("PRAGMA query_only=OFF")
        conn.execute("CREATE VIEW example_view AS SELECT id FROM example")
        conn.execute("PRAGMA query_only=ON")
        with pytest.raises(SQLiteSchemaProbeRejected):
            review_disconnected_sqlite_schema(conn, baseline)


def test_non_query_only_connection_rejected_without_modifying_it():
    conn = sqlite3.connect(":memory:")
    try:
        with pytest.raises(SQLiteSchemaProbeRejected, match="query-only"):
            capture_disconnected_sqlite_schema(conn)
        assert conn.execute("PRAGMA query_only").fetchone() == (0,)
        assert not conn.in_transaction
    finally:
        conn.close()


def test_open_transaction_rejected_without_rollback():
    conn = _db()
    try:
        conn.execute("BEGIN")
        with pytest.raises(SQLiteSchemaProbeRejected, match="idle"):
            capture_disconnected_sqlite_schema(conn)
        assert conn.in_transaction
        conn.rollback()
    finally:
        conn.close()


def test_attached_source_rejected():
    conn = _db()
    try:
        conn.execute("ATTACH DATABASE ':memory:' AS extra")
        with pytest.raises(SQLiteSchemaProbeRejected, match="single main"):
            capture_disconnected_sqlite_schema(conn)
    finally:
        conn.close()


def test_stale_and_non_exact_seal_rejected():
    with closing(_db()) as conn:
        current = capture_disconnected_sqlite_schema(conn)
        for bad in (
            replace(current, schema_sha256="A" * 64),
            replace(current, object_count=True),
            replace(current, user_version=2**31),
            replace(current, schema_version=-1),
            replace(current, schema_sha256="f" * 64),
        ):
            with pytest.raises(SQLiteSchemaProbeRejected):
                review_disconnected_sqlite_schema(conn, bad)
        with pytest.raises(SQLiteSchemaProbeRejected):
            review_disconnected_sqlite_schema(conn, {})


def test_schema_budget_rejected():
    conn = sqlite3.connect(":memory:")
    try:
        for i in range(129):
            conn.execute(f"CREATE TABLE entry_{i} (id INTEGER)")
        conn.execute("PRAGMA query_only=ON")
        with pytest.raises(SQLiteSchemaProbeRejected, match="budget"):
            capture_disconnected_sqlite_schema(conn)
        assert not conn.in_transaction
    finally:
        conn.close()


def test_instance_is_frozen_and_sqlite_connection_exact():
    with closing(_db()) as conn:
        seal = capture_disconnected_sqlite_schema(conn)
        assert isinstance(seal, DisconnectedSQLiteSchemaSeal)
        with pytest.raises(FrozenInstanceError):
            seal.schema_sha256 = "f" * 64
        with pytest.raises(SQLiteSchemaProbeRejected):
            capture_disconnected_sqlite_schema(object())


def test_excessive_schema_bytes_rejected():
    conn = sqlite3.connect(":memory:")
    try:
        for i in range(22):
            conn.execute(f"CREATE TABLE t{i} (text_{i} TEXT DEFAULT '{"a" * 3400}')")
        conn.execute("PRAGMA query_only=ON")
        with pytest.raises(SQLiteSchemaProbeRejected, match="byte budget"):
            capture_disconnected_sqlite_schema(conn)
    finally:
        conn.close()
