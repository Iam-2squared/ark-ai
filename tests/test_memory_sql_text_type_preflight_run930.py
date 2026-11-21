"""SQL-side Memory TEXT type admission before private persisted row hydration.

Disposable SQLite corruption fixtures only. No real user Memory is opened,
deleted, exported or interpreted as authenticated provenance.
"""

from __future__ import annotations

import sqlite3
from contextlib import closing

import pytest

from ark.memory.contracts import MemoryQuery, MemorySchemaError, MemoryScope, MemoryWrite
from ark.memory.sqlite_store import SQLiteMemoryStore


@pytest.mark.parametrize("column", ("content", "metadata_json", "source_id"))
@pytest.mark.parametrize("operation", ("get", "search"))
def test_nontext_persisted_memory_is_rejected_at_sql_hydration_boundary(
    tmp_path, column: str, operation: str,
) -> None:
    path = tmp_path / "isolated-memory.sqlite3"
    scope = MemoryScope("fixture-owner", "fixture-namespace")
    store = SQLiteMemoryStore(path, clock_ms=lambda: 1234)
    record = store.put(MemoryWrite(scope, "fixture-source", "fixture content"))

    # Deliberate fixture corruption: SQLite's TEXT affinity still allows
    # BLOB storage. Quick-check passes, but Python must never hydrate this
    # non-TEXT value as an otherwise valid MemoryRecord.
    with closing(sqlite3.connect(path)) as conn, conn:
        conn.execute(
            f"UPDATE memories SET {column}=CAST(? AS BLOB) WHERE memory_id=?",
            ("fixture-bytes", record.memory_id),
        )

    reopened = SQLiteMemoryStore(path, clock_ms=lambda: 1235)
    with pytest.raises(MemorySchemaError, match="stored memory row exceeds MemoryWrite bounds"):
        if operation == "get":
            reopened.get(record.memory_id, scope, include_expired=True)
        else:
            reopened.search(MemoryQuery(scope, include_expired=True))

    # The rejected read is side-effect-free and must not silently repair a
    # corrupt row or append an event on behalf of a missing external witness.
    with closing(sqlite3.connect(path)) as conn:
        assert conn.execute(
            f"SELECT typeof({column}) FROM memories WHERE memory_id=?",
            (record.memory_id,),
        ).fetchone() == ("blob",)
        assert conn.execute(
            "SELECT operation FROM memory_events ORDER BY event_id"
        ).fetchall() == [("create",)]


def test_healthy_memory_content_metadata_and_source_still_roundtrip(tmp_path) -> None:
    scope = MemoryScope("fixture-owner", "fixture-namespace")
    path = tmp_path / "healthy-memory.sqlite3"
    store = SQLiteMemoryStore(path, clock_ms=lambda: 1234)
    created = store.put(
        MemoryWrite(scope, "source-1", "valid content", {"label": "日本語"})
    )
    reopened = SQLiteMemoryStore(path, clock_ms=lambda: 1235)
    fetched = reopened.get(created.memory_id, scope)
    assert fetched is not None
    assert fetched.content == "valid content"
    assert dict(fetched.metadata) == {"label": "日本語"}
    assert [item.memory_id for item in reopened.search(MemoryQuery(scope))] == [
        created.memory_id
    ]
