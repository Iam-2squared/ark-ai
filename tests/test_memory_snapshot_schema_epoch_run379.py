"""Offline coherent Memory snapshots reject post-initialization schema drift."""

import sqlite3

import pytest

from ark.memory.coherent_snapshot_review import (
    CoherentSnapshotRequest,
    review_coherent_snapshot,
)
from ark.memory.contracts import MemorySchemaError, MemoryScope, MemoryWrite
from ark.memory.sqlite_store import SQLiteMemoryStore


def _fixture(tmp_path):
    path = tmp_path / "memory schema # percent %.sqlite"
    store = SQLiteMemoryStore(path, clock_ms=lambda: 100)
    for namespace in ("alpha", "beta"):
        store.put(MemoryWrite(MemoryScope("fixture", namespace), "source", "private fixture"))
    request = CoherentSnapshotRequest("fixture", ("alpha", "beta"))
    return store, request


@pytest.mark.parametrize(
    "tamper",
    [
        "PRAGMA user_version=2",
        "PRAGMA user_version=0",
        "DROP INDEX idx_mem_expiry",
        "ALTER TABLE memories ADD COLUMN untrusted TEXT",
        "CREATE TRIGGER untrusted AFTER INSERT ON memories BEGIN SELECT 1; END",
    ],
)
def test_snapshot_refuses_schema_changed_after_store_startup(tmp_path, tamper):
    store, request = _fixture(tmp_path)
    with sqlite3.connect(store.path) as conn:
        conn.execute(tamper)
    with pytest.raises(MemorySchemaError, match="schema"):
        review_coherent_snapshot(store, request)


def test_snapshot_no_regression_on_valid_schema_and_stable_clock(tmp_path):
    store, request = _fixture(tmp_path)
    first = review_coherent_snapshot(store, request)
    second = review_coherent_snapshot(store, request)
    assert first.provenance_sha256 == second.provenance_sha256
    assert first.records == second.records
    assert len(first.records) == 2
    assert all(len(group) == 1 for group in first.records)


def test_snapshot_does_not_recreate_missing_initialized_file(tmp_path):
    store, request = _fixture(tmp_path)
    moved = store.path.with_name("moved.sqlite")
    store.path.rename(moved)
    with pytest.raises(MemorySchemaError, match="read-only"):
        review_coherent_snapshot(store, request)
    assert not store.path.exists()


def test_snapshot_cannot_skip_schema_fence_when_query_is_empty(tmp_path):
    store, _request = _fixture(tmp_path)
    with sqlite3.connect(store.path) as conn:
        conn.execute("CREATE TABLE unexpected(note TEXT)")
    query = CoherentSnapshotRequest("fixture", ("alpha",), text="not-present")
    with pytest.raises(MemorySchemaError, match="schema"):
        review_coherent_snapshot(store, query)
