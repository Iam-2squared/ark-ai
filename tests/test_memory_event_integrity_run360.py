"""Persisted Memory v1 event reads reject corrupt storage without changing v1 clocks."""

import sqlite3

import pytest

from ark.memory import MemorySchemaError, MemoryScope, MemoryWrite, SQLiteMemoryStore


@pytest.mark.parametrize(
    ("column", "replacement"),
    [
        ("memory_id", "synthetic-corrupt-id"),
        ("revision", 0),
        ("revision", "not-an-integer"),
        ("occurred_at_ms", -1),
        ("occurred_at_ms", "not-an-integer"),
        ("operation", "CREATE"),
    ],
)
def test_memory_event_read_rejects_corrupt_storage(tmp_path, column, replacement) -> None:
    path = tmp_path / "events.sqlite3"
    store = SQLiteMemoryStore(path, clock_ms=lambda: 200)
    scope = MemoryScope("synthetic-owner", "synthetic-scope")
    store.put(MemoryWrite(scope, "synthetic-source", "private synthetic fixture"))
    with sqlite3.connect(path) as conn:
        if column == "operation":
            # Simulate on-disk tampering of the CHECK literal, not a valid app write.
            conn.execute("PRAGMA ignore_check_constraints=ON")
        assert conn.execute(
            f"UPDATE memory_events SET {column}=? WHERE event_id=1", (replacement,)
        ).rowcount == 1
    with pytest.raises(MemorySchemaError):
        store.events(scope)


def test_memory_event_clock_may_move_backward_across_sources(tmp_path) -> None:
    ticks = iter((200, 100))
    store = SQLiteMemoryStore(tmp_path / "events.sqlite3", clock_ms=lambda: next(ticks))
    scope = MemoryScope("synthetic-owner")
    store.put(MemoryWrite(scope, "first", "fixture a"))
    store.put(MemoryWrite(scope, "second", "fixture b"))
    events = store.events(scope)
    assert [item.event_id for item in events] == [1, 2]
    assert [item.occurred_at_ms for item in events] == [200, 100]
    assert [item.operation for item in events] == ["create", "create"]


def test_memory_event_pagination_and_content_free_history(tmp_path) -> None:
    store = SQLiteMemoryStore(tmp_path / "events.sqlite3", clock_ms=lambda: 1234)
    scope = MemoryScope("synthetic-owner")
    record = store.put(MemoryWrite(scope, "item", "do-not-log-private-content"))
    store.put(MemoryWrite(scope, "item", "updated-content"), expected_revision=1)
    assert store.delete(record.memory_id, scope, expected_revision=2)
    events = store.events(scope, limit=2)
    assert [item.operation for item in events] == ["create", "update"]
    tail = store.events(scope, after_event_id=events[-1].event_id)
    assert [item.operation for item in tail] == ["delete"]
    assert "do-not-log-private-content" not in repr(events + tail)
