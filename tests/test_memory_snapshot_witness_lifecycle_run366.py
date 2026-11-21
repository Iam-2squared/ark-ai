"""Content-free coherent witness also binds metadata and lifecycle values."""

import sqlite3

import pytest

from ark.memory import MemoryScope, MemoryWrite, SQLiteMemoryStore
from ark.memory.coherent_snapshot_review import (
    CoherentSnapshotRequest,
    review_coherent_snapshot,
)


@pytest.mark.parametrize(
    ("column", "new_value"),
    [
        ("metadata_json", '{"purpose":"new"}'),
        ("created_at_ms", 99),
        ("expires_at_ms", 900),
    ],
)
def test_lifecycle_changes_cannot_reuse_an_old_snapshot_digest(
    tmp_path, column, new_value
):
    store = SQLiteMemoryStore(tmp_path / "memory.db", clock_ms=lambda: 100)
    scope = MemoryScope("fixture-owner", "fixture-namespace")
    item = store.put(MemoryWrite(scope, "fixture-source", "secret-content"))
    request = CoherentSnapshotRequest(scope.owner_id, (scope.namespace,))
    before = review_coherent_snapshot(store, request)
    assert before.records[0][0].memory_id == item.memory_id

    with sqlite3.connect(store.path) as conn:
        conn.execute(
            f"UPDATE memories SET {column}=? WHERE memory_id=?",
            (new_value, item.memory_id),
        )

    after = review_coherent_snapshot(store, request)
    assert before.provenance_sha256 != after.provenance_sha256
    assert before.records[0][0].content_sha256 == after.records[0][0].content_sha256
    assert before.records[0][0].revision == after.records[0][0].revision
    assert before.records[0][0].updated_at_ms == after.records[0][0].updated_at_ms
    assert "secret-content" not in after.provenance_sha256
    with sqlite3.connect(store.path) as conn:
        assert conn.execute("PRAGMA user_version").fetchone()[0] == 1


def test_unchanged_memory_snapshot_stays_deterministic(tmp_path):
    store = SQLiteMemoryStore(tmp_path / "memory.db", clock_ms=lambda: 100)
    scope = MemoryScope("fixture-owner", "fixture-namespace")
    store.put(MemoryWrite(scope, "fixture-source", "private", {"origin": "fixture"}))
    request = CoherentSnapshotRequest(scope.owner_id, (scope.namespace,))
    first = review_coherent_snapshot(store, request)
    second = review_coherent_snapshot(store, request)
    assert first.provenance_sha256 == second.provenance_sha256
    assert len(first.provenance_sha256) == 64
