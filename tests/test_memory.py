import sqlite3

import pytest

from ark.memory import (
    MemoryConflictError,
    MemoryQuery,
    MemorySchemaError,
    MemoryScope,
    MemoryWrite,
    SQLiteMemoryStore,
    deterministic_memory_id,
)


def test_deterministic_id_is_scope_and_source_isolated() -> None:
    left = MemoryScope("person-a", "profile")
    right = MemoryScope("person-b", "profile")
    assert deterministic_memory_id(left, "favorite-color") == deterministic_memory_id(
        left, "favorite-color"
    )
    assert deterministic_memory_id(left, "favorite-color") != deterministic_memory_id(
        left, "favorite-food"
    )
    assert deterministic_memory_id(left, "favorite-color") != deterministic_memory_id(
        right, "favorite-color"
    )


def test_create_get_and_content_free_audit(tmp_path) -> None:
    store = SQLiteMemoryStore(tmp_path / "memory.sqlite3", clock_ms=lambda: 1000)
    scope = MemoryScope("person-a", "profile")
    record = store.put(
        MemoryWrite(
            scope=scope,
            source_id="favorite-color",
            content="blue",
            metadata={"origin": "user"},
        )
    )
    assert record.revision == 1
    assert store.get(record.memory_id, scope) == record
    events = store.events(scope)
    assert [(event.operation, event.revision) for event in events] == [("create", 1)]
    assert "blue" not in repr(events)
    assert "origin" not in repr(events)


def test_put_requires_exact_compare_and_swap_revision(tmp_path) -> None:
    store = SQLiteMemoryStore(tmp_path / "memory.sqlite3", clock_ms=lambda: 1000)
    scope = MemoryScope("person-a")
    first = store.put(MemoryWrite(scope, "timezone", "JST"))
    with pytest.raises(MemoryConflictError):
        store.put(MemoryWrite(scope, "timezone", "UTC"))
    with pytest.raises(MemoryConflictError):
        store.put(MemoryWrite(scope, "timezone", "UTC"), expected_revision=9)

    second = store.put(
        MemoryWrite(scope, "timezone", "Asia/Tokyo"),
        expected_revision=first.revision,
    )
    assert second.memory_id == first.memory_id
    assert second.revision == 2
    assert second.created_at_ms == first.created_at_ms


def test_scope_isolation_applies_to_get_search_and_events(tmp_path) -> None:
    store = SQLiteMemoryStore(tmp_path / "memory.sqlite3", clock_ms=lambda: 1000)
    left = MemoryScope("person-a", "private")
    right = MemoryScope("person-b", "private")
    record = store.put(MemoryWrite(left, "note-1", "launch checklist"))

    assert store.get(record.memory_id, right) is None
    assert store.search(MemoryQuery(right, "launch")) == []
    assert store.events(right) == []


def test_expired_records_are_hidden_and_physically_purgeable(tmp_path) -> None:
    now = {"value": 1000}
    store = SQLiteMemoryStore(tmp_path / "memory.sqlite3", clock_ms=lambda: now["value"])
    scope = MemoryScope("person-a")
    record = store.put(MemoryWrite(scope, "temporary", "short lived", expires_at_ms=1500))
    assert store.get(record.memory_id, scope) is not None

    now["value"] = 1500
    assert store.get(record.memory_id, scope) is None
    assert store.get(record.memory_id, scope, include_expired=True) is not None
    assert store.purge_expired(scope=scope) == 1
    assert store.get(record.memory_id, scope, include_expired=True) is None
    assert store.events(scope)[-1].operation == "expire"


def test_lexical_search_is_deterministic_and_ranked(tmp_path) -> None:
    ticks = iter([1000, 2000, 3000, 4000])
    store = SQLiteMemoryStore(tmp_path / "memory.sqlite3", clock_ms=lambda: next(ticks))
    scope = MemoryScope("person-a")
    store.put(MemoryWrite(scope, "a", "alpha beta"))
    store.put(MemoryWrite(scope, "b", "alpha beta gamma"))
    store.put(MemoryWrite(scope, "c", "alpha only"))

    found = store.search(MemoryQuery(scope, "alpha beta", limit=3))
    assert [item.source_id for item in found] == ["b", "a", "c"]


def test_lexical_search_supports_cjk_bigrams(tmp_path) -> None:
    store = SQLiteMemoryStore(tmp_path / "memory.sqlite3", clock_ms=lambda: 1000)
    scope = MemoryScope("person-a")
    store.put(MemoryWrite(scope, "fruit", "好きな果物は青いりんごです"))
    store.put(MemoryWrite(scope, "weather", "今日は晴れです"))

    found = store.search(MemoryQuery(scope, "青いりんご"))
    assert [item.source_id for item in found] == ["fruit"]


def test_delete_is_physical_and_revision_guarded(tmp_path) -> None:
    store = SQLiteMemoryStore(tmp_path / "memory.sqlite3", clock_ms=lambda: 1000)
    scope = MemoryScope("person-a")
    record = store.put(MemoryWrite(scope, "secret", "erase me"))
    with pytest.raises(MemoryConflictError):
        store.delete(record.memory_id, scope, expected_revision=2)

    assert store.delete(record.memory_id, scope, expected_revision=1) is True
    assert store.get(record.memory_id, scope, include_expired=True) is None
    assert store.delete(record.memory_id, scope, expected_revision=1) is False
    assert store.events(scope)[-1].operation == "delete"


def test_newer_database_schema_fails_closed(tmp_path) -> None:
    path = tmp_path / "memory.sqlite3"
    with sqlite3.connect(path) as conn:
        conn.execute("PRAGMA user_version = 999")
    with pytest.raises(MemorySchemaError):
        SQLiteMemoryStore(path)
