"""Schema-only SQLite observations cannot gain custody via monkeypatches."""

import sqlite3
from contextlib import closing
from dataclasses import replace

import pytest

from ark.disconnected_sqlite_schema_probe import (
    DisconnectedSQLiteSchemaSeal,
    SQLiteSchemaProbeRejected,
    capture_disconnected_sqlite_schema,
    review_disconnected_sqlite_schema,
)

_DENIALS = (
    "source_authenticated",
    "independent_custody_proven",
    "wal_snapshot_verified",
    "cross_store_atomicity_proven",
    "application_data_disclosure_authorized",
)


def _connection():
    db = sqlite3.connect(":memory:")
    db.execute("CREATE TABLE fixture (id INTEGER PRIMARY KEY)")
    db.execute("PRAGMA query_only=ON")
    return db


@pytest.mark.parametrize("name", _DENIALS)
def test_original_denial_descriptor_not_replaceable_with_false(monkeypatch, name):
    with closing(_connection()) as db:
        original = capture_disconnected_sqlite_schema(db)
        monkeypatch.setattr(
            DisconnectedSQLiteSchemaSeal, name, property(lambda self: False),
        )
        with pytest.raises(SQLiteSchemaProbeRejected, match="acquired authority"):
            capture_disconnected_sqlite_schema(db)
        with pytest.raises(SQLiteSchemaProbeRejected, match="acquired authority"):
            review_disconnected_sqlite_schema(db, original)
        assert not db.in_transaction


def test_forged_dataclass_equality_cannot_hide_stale_seal(monkeypatch):
    with closing(_connection()) as db:
        original = capture_disconnected_sqlite_schema(db)
        stale = replace(original, schema_sha256="f" * 64)
        monkeypatch.setattr(
            DisconnectedSQLiteSchemaSeal, "__eq__", lambda self, other: True,
        )
        with pytest.raises(SQLiteSchemaProbeRejected, match="differ"):
            review_disconnected_sqlite_schema(db, stale)


def test_forged_dataclass_inequality_does_not_reject_same_schema(monkeypatch):
    with closing(_connection()) as db:
        original = capture_disconnected_sqlite_schema(db)
        monkeypatch.setattr(
            DisconnectedSQLiteSchemaSeal, "__eq__", lambda self, other: False,
        )
        verified = review_disconnected_sqlite_schema(db, original)
        assert verified.schema_sha256 == original.schema_sha256
        assert verified.object_count == original.object_count
        assert verified.cross_store_atomicity_proven is False
        assert not db.in_transaction
