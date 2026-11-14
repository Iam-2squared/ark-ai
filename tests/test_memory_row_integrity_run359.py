"""Reject synthetic SQLite row tampering without altering frozen schema v1."""

import sqlite3

import pytest

from ark.memory import MemoryQuery, MemorySchemaError, MemoryScope, MemoryWrite, SQLiteMemoryStore


@pytest.mark.parametrize(
    ("column", "replacement"),
    [
        ("content", "modified-content"),
        ("content_sha256", "0" * 64),
        ("source_id", "substituted-source"),
        ("metadata_json", '{"b":"two","a":"one"}'),
        ("created_at_ms", "not-an-integer"),
        ("updated_at_ms", "not-an-integer"),
        ("expires_at_ms", "not-an-integer"),
        ("revision", "not-an-integer"),
    ],
)
def test_corrupt_stored_row_fails_closed_on_get_and_search(
    tmp_path, column: str, replacement: object
) -> None:
    path = tmp_path / "memory.sqlite3"
    store = SQLiteMemoryStore(path, clock_ms=lambda: 1000)
    scope = MemoryScope("synthetic-owner", "synthetic-namespace")
    record = store.put(
        MemoryWrite(scope, "synthetic-source", "fixture-content", {"a": "one", "b": "two"})
    )
    assert column in {
        "content", "content_sha256", "source_id", "metadata_json", "created_at_ms",
        "updated_at_ms", "expires_at_ms", "revision",
    }
    with sqlite3.connect(path) as conn:
        conn.execute(
            f"UPDATE memories SET {column}=? WHERE memory_id=?", (replacement, record.memory_id)
        )
    with pytest.raises(MemorySchemaError):
        store.get(record.memory_id, scope, include_expired=True)
    with pytest.raises(MemorySchemaError):
        store.search(MemoryQuery(scope, include_expired=True))


def test_replaced_stored_memory_id_fails_digest_identity_check(tmp_path) -> None:
    path = tmp_path / "memory.sqlite3"
    store = SQLiteMemoryStore(path, clock_ms=lambda: 1000)
    scope = MemoryScope("synthetic-owner")
    record = store.put(MemoryWrite(scope, "synthetic-source", "fixture-content"))
    forged_id = "mem_" + "0" * 64
    assert record.memory_id != forged_id
    with sqlite3.connect(path) as conn:
        conn.execute(
            "UPDATE memories SET memory_id=? WHERE memory_id=?", (forged_id, record.memory_id)
        )
    with pytest.raises(MemorySchemaError, match="identity"):
        store.get(forged_id, scope, include_expired=True)


def test_canonical_memory_rows_remain_readable_without_migration(tmp_path) -> None:
    path = tmp_path / "memory.sqlite3"
    store = SQLiteMemoryStore(path, clock_ms=lambda: 1000)
    scope = MemoryScope("synthetic-owner", "synthetic-namespace")
    record = store.put(
        MemoryWrite(scope, "synthetic-source", "fixture-content", {"b": "two", "a": "one"})
    )
    assert store.get(record.memory_id, scope) == record
    assert store.search(MemoryQuery(scope))[0] == record
    with sqlite3.connect(path) as conn:
        assert conn.execute("PRAGMA user_version").fetchone()[0] == 1
