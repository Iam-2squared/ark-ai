"""A detached SQLite schema hash can never authorize access or disclosure."""

from __future__ import annotations

import sqlite3
from contextlib import closing

import pytest

from ark.disconnected_sqlite_schema_probe import (
    DisconnectedSQLiteSchemaSeal,
    SQLiteSchemaProbeRejected,
    capture_disconnected_sqlite_schema,
    review_disconnected_sqlite_schema,
)


def _connection():
    conn = sqlite3.connect(":memory:")
    conn.execute("CREATE TABLE fixture (id INTEGER PRIMARY KEY)")
    conn.execute("PRAGMA query_only=ON")
    return conn


@pytest.mark.parametrize(
    "flag",
    (
        "source_authenticated",
        "independent_custody_proven",
        "wal_snapshot_verified",
        "cross_store_atomicity_proven",
        "application_data_disclosure_authorized",
    ),
)
def test_capture_rejects_exact_type_authority_spoof(monkeypatch, flag):
    with closing(_connection()) as conn:
        monkeypatch.setattr(
            DisconnectedSQLiteSchemaSeal, flag, property(lambda self: True),
        )
        with pytest.raises(SQLiteSchemaProbeRejected, match="acquired authority"):
            capture_disconnected_sqlite_schema(conn)
        assert not conn.in_transaction


@pytest.mark.parametrize(
    "flag",
    (
        "source_authenticated",
        "independent_custody_proven",
        "wal_snapshot_verified",
        "cross_store_atomicity_proven",
        "application_data_disclosure_authorized",
    ),
)
def test_review_rejects_retained_authority_spoof(monkeypatch, flag):
    with closing(_connection()) as conn:
        retained = capture_disconnected_sqlite_schema(conn)
        monkeypatch.setattr(
            DisconnectedSQLiteSchemaSeal, flag, property(lambda self: True),
        )
        with pytest.raises(SQLiteSchemaProbeRejected, match="acquired authority"):
            review_disconnected_sqlite_schema(conn, retained)


def test_valid_schema_remains_metadata_only():
    with closing(_connection()) as conn:
        retained = capture_disconnected_sqlite_schema(conn)
        assert review_disconnected_sqlite_schema(conn, retained) == retained
        assert retained.source_authenticated is False
        assert retained.independent_custody_proven is False
        assert retained.wal_snapshot_verified is False
        assert retained.cross_store_atomicity_proven is False
        assert retained.application_data_disclosure_authorized is False
