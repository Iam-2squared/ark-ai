"""Atomic, content-free Memory v1 event lifecycle consistency regressions."""

from __future__ import annotations

import sqlite3

import pytest

from ark.memory.atomic_epoch_review import review_atomic_memory_epoch
from ark.memory.contracts import MemorySchemaError, MemoryScope, MemoryWrite
from ark.memory.sqlite_store import SQLiteMemoryStore


def _store(tmp_path):
    return SQLiteMemoryStore(tmp_path / "epoch.sqlite", clock_ms=lambda: 1000)


def _put(store, scope, source="source", *, revision=0, expiry=None):
    return store.put(
        MemoryWrite(
            scope, source, "secret payload",
            expires_at_ms=expiry,
        ),
        expected_revision=revision,
    )


def _modify(store, sql):
    with sqlite3.connect(store.path) as conn:
        conn.execute(sql)


def test_create_update_delete_recreate_lifecycle_is_supported(tmp_path):
    store = _store(tmp_path)
    scope = MemoryScope("one-owner", "notes")
    first = _put(store, scope)
    _put(store, scope, revision=1)
    assert store.delete(first.memory_id, scope, expected_revision=2)
    rebuilt = _put(store, scope)
    assert rebuilt.revision == 1
    reviewed = review_atomic_memory_epoch(store, (scope,))
    assert reviewed.row_counts == (1,)
    assert reviewed.event_counts == (4,)
    assert "secret payload" not in repr(reviewed)
    assert reviewed.dispatch_authorized is False


def test_interleaved_namespaces_are_not_mistaken_for_missing_events(tmp_path):
    store = _store(tmp_path)
    first_scope = MemoryScope("one-owner", "a")
    second_scope = MemoryScope("one-owner", "b")
    _put(store, first_scope)
    _put(store, second_scope)
    _put(store, first_scope, revision=1)
    reviewed = review_atomic_memory_epoch(store, (first_scope, second_scope))
    assert reviewed.event_counts == (2, 1)
    assert reviewed.row_counts == (1, 1)


@pytest.mark.parametrize("corruption", [
    "UPDATE memory_events SET operation='update' WHERE event_id=1",
    "UPDATE memory_events SET revision=2 WHERE event_id=1",
    "DELETE FROM memory_events WHERE event_id=1",
    "UPDATE memories SET revision=2",
])
def test_orphan_lifecycle_and_live_row_revision_are_denied(tmp_path, corruption):
    store = _store(tmp_path)
    scope = MemoryScope("one-owner", "notes")
    _put(store, scope)
    _modify(store, corruption)
    with pytest.raises(MemorySchemaError, match="event lifecycle|live rows"):
        review_atomic_memory_epoch(store, (scope,))


def test_skipped_update_revision_is_denied(tmp_path):
    store = _store(tmp_path)
    scope = MemoryScope("one-owner", "notes")
    _put(store, scope)
    _put(store, scope, revision=1)
    _modify(store, "UPDATE memory_events SET revision=3 WHERE operation='update'")
    with pytest.raises(MemorySchemaError, match="event lifecycle"):
        review_atomic_memory_epoch(store, (scope,))


def test_stale_terminal_event_revision_is_denied(tmp_path):
    store = _store(tmp_path)
    scope = MemoryScope("one-owner", "notes")
    record = _put(store, scope)
    _put(store, scope, revision=1)
    assert store.delete(record.memory_id, scope, expected_revision=2)
    _modify(store, "UPDATE memory_events SET revision=1 WHERE operation='delete'")
    with pytest.raises(MemorySchemaError, match="event lifecycle"):
        review_atomic_memory_epoch(store, (scope,))


def test_terminal_event_must_not_hide_surviving_live_row(tmp_path):
    store = _store(tmp_path)
    scope = MemoryScope("one-owner", "notes")
    _put(store, scope)
    _modify(store, "INSERT INTO memory_events("
                    "memory_id,owner_id,namespace,operation,revision,occurred_at_ms"
                    ") SELECT memory_id,owner_id,namespace,'expire',1,1000 FROM memories")
    with pytest.raises(MemorySchemaError, match="live rows"):
        review_atomic_memory_epoch(store, (scope,))


def test_expiry_terminal_event_is_valid(tmp_path):
    store = _store(tmp_path)
    scope = MemoryScope("one-owner", "notes")
    _put(store, scope, expiry=900)
    assert store.purge_expired(scope=scope) == 1
    reviewed = review_atomic_memory_epoch(store, (scope,))
    assert reviewed.row_counts == (0,)
    assert reviewed.event_counts == (2,)
