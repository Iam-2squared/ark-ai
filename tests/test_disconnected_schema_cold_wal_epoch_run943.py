"""Run943: detached SQLite schema evidence across cold Python and WAL epochs.

These are strictly local fixture schemas. A matching schema digest is not an
authenticated provenance, privacy consent, or a durable external audit.
"""

from __future__ import annotations

import json
import sqlite3
import subprocess
import sys

import pytest

from ark.disconnected_sqlite_schema_probe import (
    SQLiteSchemaProbeRejected,
    capture_disconnected_sqlite_schema,
    review_disconnected_sqlite_schema,
)

_CHILD = """
import json
import sqlite3
import sys
from ark.disconnected_sqlite_schema_probe import capture_disconnected_sqlite_schema

connection = sqlite3.connect(sys.argv[1])
try:
    connection.execute("PRAGMA query_only=ON")
    seal = capture_disconnected_sqlite_schema(connection)
    print(json.dumps((seal.schema_sha256, seal.object_count,
                      seal.user_version, seal.schema_version)))
finally:
    connection.close()
"""


@pytest.mark.parametrize("indexed", (False, True))
def test_cold_process_schema_evidence_is_exact_and_non_authorizing(tmp_path, indexed):
    path = tmp_path / "synthetic-schema.sqlite3"
    with sqlite3.connect(path) as writer:
        writer.execute("CREATE TABLE synthetic_fixture(id INTEGER PRIMARY KEY, value TEXT)")
        if indexed:
            writer.execute("CREATE INDEX idx_fixture_value ON synthetic_fixture(value)")
        writer.execute("PRAGMA user_version=17")
        writer.commit()

    with sqlite3.connect(path) as reader:
        reader.execute("PRAGMA query_only=ON")
        local = capture_disconnected_sqlite_schema(reader)
        assert local.source_authenticated is False
        assert local.wal_snapshot_verified is False
        assert local.application_data_disclosure_authorized is False

    child = subprocess.run(
        [sys.executable, "-c", _CHILD, str(path)],
        capture_output=True,
        text=True,
        check=True,
        timeout=20,
    )
    reported = json.loads(child.stdout)
    assert tuple(reported) == (
        local.schema_sha256, local.object_count,
        local.user_version, local.schema_version,
    )
    assert "synthetic_fixture" not in child.stdout
    assert len(local.schema_sha256) == 64


def test_wal_schema_commit_invalidates_prior_seal_only_after_commit(tmp_path):
    path = tmp_path / "synthetic-wal-schema.sqlite3"
    writer = sqlite3.connect(path)
    reader = sqlite3.connect(path)
    try:
        assert writer.execute("PRAGMA journal_mode=WAL").fetchone() == ("wal",)
        writer.execute("CREATE TABLE synthetic_fixture(id INTEGER PRIMARY KEY)")
        writer.commit()
        reader.execute("PRAGMA query_only=ON")
        retained = capture_disconnected_sqlite_schema(reader)

        # The separate read-only connection cannot see an uncommitted DDL.
        writer.execute("BEGIN IMMEDIATE")
        writer.execute("CREATE TABLE pending_fixture(id TEXT)")
        assert review_disconnected_sqlite_schema(reader, retained) == retained
        writer.commit()

        with pytest.raises(SQLiteSchemaProbeRejected, match="differ"):
            review_disconnected_sqlite_schema(reader, retained)
        changed = capture_disconnected_sqlite_schema(reader)
        assert changed.schema_sha256 != retained.schema_sha256
        assert changed.object_count == retained.object_count + 1
        assert changed.source_authenticated is False
    finally:
        reader.close()
        writer.close()
