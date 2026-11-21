"""Synthetic schema probe helpers cannot be replaced ahead of SQL reads.

Only isolated SQLite :memory: fixtures are inspected. No private rows,
persistent store, user path, permission or disclosure is involved.
"""

from __future__ import annotations

import sqlite3
from contextlib import closing

import pytest

from ark import disconnected_sqlite_schema_probe as schema


def _fixture():
    db = sqlite3.connect(":memory:")
    db.execute("CREATE TABLE fixture (id INTEGER PRIMARY KEY, note TEXT)")
    db.execute("PRAGMA query_only=ON")
    return db


@pytest.mark.parametrize(
    "helper",
    ("_state", "_seal_fields", "_assert_inert_seal"),
)
@pytest.mark.parametrize("operation", ("capture", "review"))
def test_changed_schema_helper_denied_before_sqlite_transaction(
    monkeypatch, helper, operation,
):
    with closing(_fixture()) as db:
        baseline = schema.capture_disconnected_sqlite_schema(db)
        touched = []

        def poison(*_args, **_kwargs):
            touched.append(helper)
            raise AssertionError("substituted schema callback invoked")

        with monkeypatch.context() as patch:
            patch.setattr(schema, helper, poison)
            with pytest.raises(
                schema.SQLiteSchemaProbeRejected, match="contract changed",
            ):
                if operation == "capture":
                    schema.capture_disconnected_sqlite_schema(db)
                else:
                    schema.review_disconnected_sqlite_schema(db, baseline)
        assert touched == []
        assert not db.in_transaction


def test_unchanged_schema_and_original_receipt_remain_deny_only():
    with closing(_fixture()) as db:
        retained = schema.capture_disconnected_sqlite_schema(db)
        current = schema.review_disconnected_sqlite_schema(db, retained)
        assert current.schema_sha256 == retained.schema_sha256
        assert current.application_data_disclosure_authorized is False
        assert current.wal_snapshot_verified is False
        assert current.cross_store_atomicity_proven is False
        assert not db.in_transaction
