"""Detached schema review admits bounded retained digests before SQLite access.

These memory-only metadata snapshots do not authenticate a database, reveal
application records, grant consent, or authorize execution.
"""

from __future__ import annotations

import sqlite3
from contextlib import closing
from dataclasses import replace

import pytest

from ark.disconnected_sqlite_schema_probe import (
    SQLiteSchemaProbeRejected,
    capture_disconnected_sqlite_schema,
    review_disconnected_sqlite_schema,
)


@pytest.mark.parametrize(
    "malformed",
    (
        "",
        "a" * 63,
        "a" * 65,
        "a" * 100_000,
        "あ" * 100_000,
    ),
)
def test_reject_retained_schema_hash_outside_exact_width_before_begin(
    malformed: str,
) -> None:
    with closing(sqlite3.connect(":memory:")) as connection:
        connection.execute("CREATE TABLE t (id INTEGER PRIMARY KEY)")
        connection.execute("PRAGMA query_only=ON")
        baseline = capture_disconnected_sqlite_schema(connection)
        bad = replace(baseline, schema_sha256=malformed)
        with pytest.raises(SQLiteSchemaProbeRejected, match="invalid retained schema seal"):
            review_disconnected_sqlite_schema(connection, bad)
        assert not connection.in_transaction
        assert connection.execute("PRAGMA query_only").fetchone() == (1,)
        assert review_disconnected_sqlite_schema(connection, baseline) == baseline
        assert baseline.application_data_disclosure_authorized is False
        assert baseline.wal_snapshot_verified is False
