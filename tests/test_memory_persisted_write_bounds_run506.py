"""Persisted Memory v1 rows obey the same limits as canonical writes.

This checks malformed but hash-consistent local SQLite data, not provenance,
secure erasure, independent history custody, or an authorized read.
"""

import hashlib
import json
import sqlite3

import pytest

from ark.memory import (
    MemoryQuery,
    MemorySchemaError,
    MemoryScope,
    MemoryWrite,
    SQLiteMemoryStore,
    deterministic_memory_id,
)


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("metadata", {f"k{i}": "x" for i in range(65)}),
        ("metadata", {" ": "value"}),
        ("metadata", {"k" * 4097: "value"}),
        ("metadata", {"key": "v" * 4097}),
        ("content", ""),
        ("content", "x" * 1_000_001),
        ("source", "s" * 513),
    ],
)
def test_hash_consistent_out_of_budget_sqlite_row_denied(tmp_path, field, value):
    path = tmp_path / "memory.sqlite3"
    store = SQLiteMemoryStore(path, clock_ms=lambda: 1000)
    scope = MemoryScope("fixture-owner", "fixture-namespace")
    original = store.put(MemoryWrite(scope, "source", "fixture", {"valid": "yes"}))
    memory_id = original.memory_id
    with sqlite3.connect(path) as conn:
        if field == "metadata":
            data = json.dumps(value, sort_keys=True, separators=(",", ":"))
            conn.execute(
                "UPDATE memories SET metadata_json=? WHERE memory_id=?",
                (data, memory_id),
            )
        elif field == "content":
            digest = hashlib.sha256(value.encode("utf-8")).hexdigest()
            conn.execute(
                "UPDATE memories SET content=?, content_sha256=? WHERE memory_id=?",
                (value, digest, memory_id),
            )
        else:
            new_id = deterministic_memory_id(scope, value)
            conn.execute(
                "UPDATE memories SET source_id=?, memory_id=? WHERE memory_id=?",
                (value, new_id, memory_id),
            )
            memory_id = new_id
    with pytest.raises(MemorySchemaError, match="MemoryWrite bounds"):
        store.get(memory_id, scope, include_expired=True)
    with pytest.raises(MemorySchemaError, match="MemoryWrite bounds"):
        store.search(MemoryQuery(scope, include_expired=True))
    with sqlite3.connect(path) as conn:
        assert conn.execute("SELECT count(*) FROM memories").fetchone() == (1,)
        assert conn.execute("SELECT count(*) FROM memory_events").fetchone() == (1,)


def test_valid_maximum_metadata_budget_remains_readable(tmp_path):
    path = tmp_path / "memory.sqlite3"
    store = SQLiteMemoryStore(path, clock_ms=lambda: 1000)
    scope = MemoryScope("fixture-owner")
    metadata = {f"key{i}": "v" * 4096 for i in range(64)}
    recorded = store.put(MemoryWrite(scope, "source", "fixture", metadata))
    assert dict(store.get(recorded.memory_id, scope).metadata) == metadata
    assert store.search(MemoryQuery(scope))[0].memory_id == recorded.memory_id
