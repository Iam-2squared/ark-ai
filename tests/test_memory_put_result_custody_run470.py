"""Memory post-COMMIT result identity is diagnostic, never rollback proof."""

from __future__ import annotations

import sqlite3
from types import MappingProxyType, SimpleNamespace

import pytest

import ark.memory.sqlite_store as storage
from ark.memory import MemorySchemaError, MemoryScope, MemoryWrite


def _fixture(tmp_path):
    path = tmp_path / "memory.sqlite"
    store = storage.SQLiteMemoryStore(path, clock_ms=lambda: 100)
    scope = MemoryScope("synthetic-owner", "synthetic-private")
    return path, store, scope


def _different_equal(value):
    other = ("~" + value)[1:]
    assert other == value and other is not value
    return other


def test_unchanged_put_result_is_original_memory_record(tmp_path):
    path, store, scope = _fixture(tmp_path)
    result = store.put(MemoryWrite(scope, "source-identity", "synthetic text", {"tag": "a"}))
    assert type(result) is storage.MemoryRecord
    assert type(result.metadata) is MappingProxyType
    assert result.revision == 1
    with sqlite3.connect(path) as conn:
        assert conn.execute("SELECT COUNT(*) FROM memories").fetchone()[0] == 1
        assert conn.execute("SELECT COUNT(*) FROM memory_events").fetchone()[0] == 1


@pytest.mark.parametrize(
    "forgery",
    (
        "duck", "subclass", "equal-content", "equal-source",
        "scope-clone", "changed-metadata", "revision",
    ),
)
def test_created_record_forgery_fails_after_durable_commit(tmp_path, monkeypatch, forgery):
    path, store, scope = _fixture(tmp_path)
    original = storage.MemoryRecord

    class ForgedRecord(original):
        pass

    def injected(*args):
        record = original(*args)
        if forgery == "duck":
            return SimpleNamespace(
                memory_id=record.memory_id,
                scope=record.scope,
                source_id=record.source_id,
                content=record.content,
                dispatch_authorized=True,
            )
        if forgery == "subclass":
            return ForgedRecord(*args)
        if forgery == "equal-content":
            object.__setattr__(record, "content", _different_equal(record.content))
        elif forgery == "equal-source":
            object.__setattr__(record, "source_id", _different_equal(record.source_id))
        elif forgery == "scope-clone":
            object.__setattr__(
                record, "scope",
                MemoryScope(record.scope.owner_id, record.scope.namespace),
            )
        elif forgery == "changed-metadata":
            object.__setattr__(record, "metadata", MappingProxyType({"tag": "wrong"}))
        elif forgery == "revision":
            object.__setattr__(record, "revision", 999)
        return record

    monkeypatch.setattr(storage, "MemoryRecord", injected)
    with pytest.raises(MemorySchemaError, match="put result changed after commit"):
        store.put(MemoryWrite(scope, "source-identity", "synthetic private content",
                              {"tag": "a"}))
    with sqlite3.connect(path) as conn:
        rows = conn.execute("SELECT content,revision FROM memories").fetchall()
        events = conn.execute("SELECT operation,revision FROM memory_events").fetchall()
    assert rows == [("synthetic private content", 1)]
    assert events == [("create", 1)]


def test_update_result_forgery_preserves_committed_revision_and_event(tmp_path, monkeypatch):
    path, store, scope = _fixture(tmp_path)
    initial = store.put(MemoryWrite(scope, "source-identity", "initial text"))
    original = storage.MemoryRecord
    constructor_calls = 0

    def injected(*args):
        nonlocal constructor_calls
        constructor_calls += 1
        result = original(*args)
        # First constructor hydrates the previous row before the transaction
        # commits. Only the second constructor is the returned post-COMMIT row.
        if constructor_calls == 2:
            object.__setattr__(result, "revision", 999)
        return result

    monkeypatch.setattr(storage, "MemoryRecord", injected)
    with pytest.raises(MemorySchemaError, match="put result changed after commit"):
        store.put(
            MemoryWrite(scope, "source-identity", "committed replacement"),
            expected_revision=initial.revision,
        )
    with sqlite3.connect(path) as conn:
        rows = conn.execute("SELECT content,revision FROM memories").fetchall()
        events = conn.execute(
            "SELECT operation,revision FROM memory_events ORDER BY event_id"
        ).fetchall()
    assert rows == [("committed replacement", 2)]
    assert events == [("create", 1), ("update", 2)]
