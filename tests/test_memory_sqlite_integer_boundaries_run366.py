"""Memory v1 preserves SQLite signed-64-bit boundaries on all write paths."""

import sqlite3

import pytest

from ark.memory import (
    MemoryConflictError,
    MemoryScope,
    MemoryWrite,
    SQLiteMemoryStore,
)

MAX = (1 << 63) - 1


@pytest.mark.parametrize("bad_expiry", [-1, True, MAX + 1, 1 << 80])
def test_expiry_rejected_before_sqlite_binding(bad_expiry):
    with pytest.raises(ValueError, match="expires_at_ms"):
        MemoryWrite(
            MemoryScope("fixture-owner"),
            "fixture-source",
            "fixture-content",
            expires_at_ms=bad_expiry,
        )


@pytest.mark.parametrize("operation", ["create", "update", "delete", "purge"])
def test_bad_clock_is_rejected_before_any_mutation(tmp_path, operation):
    store = SQLiteMemoryStore(tmp_path / "memory.db", clock_ms=lambda: 1)
    scope = MemoryScope("fixture-owner")
    prior = None
    if operation != "create":
        prior = store.put(
            MemoryWrite(scope, "fixture-source", "safe", expires_at_ms=3)
        )
    store._clock_ms = lambda: MAX + 1
    with pytest.raises(ValueError, match="clock_ms"):
        if operation == "create":
            store.put(MemoryWrite(scope, "fixture-new", "value"))
        elif operation == "update":
            store.put(
                MemoryWrite(scope, "fixture-source", "other"),
                expected_revision=prior.revision,
            )
        elif operation == "delete":
            store.delete(prior.memory_id, scope, expected_revision=1)
        else:
            store.purge_expired(scope=scope)

    with sqlite3.connect(store.path) as conn:
        assert conn.execute("SELECT COUNT(*) FROM memories").fetchone()[0] == (
            0 if operation == "create" else 1
        )
        assert conn.execute("SELECT COUNT(*) FROM memory_events").fetchone()[0] == (
            0 if operation == "create" else 1
        )


def test_valid_sqlite_integer_maximum_is_accepted(tmp_path):
    store = SQLiteMemoryStore(tmp_path / "memory.db", clock_ms=lambda: MAX)
    scope = MemoryScope("fixture-owner")
    item = store.put(MemoryWrite(scope, "fixture-source", "text", expires_at_ms=MAX))
    assert item.updated_at_ms == MAX
    assert store.get(item.memory_id, scope, include_expired=True) == item
    assert store.get(item.memory_id, scope) is None
    assert len(store.events(scope)) == 1
    assert store.events(scope, after_event_id=MAX) == []


def test_maximum_revision_rejects_increment_without_mutating(tmp_path):
    store = SQLiteMemoryStore(tmp_path / "memory.db", clock_ms=lambda: 100)
    scope = MemoryScope("fixture-owner")
    item = store.put(MemoryWrite(scope, "fixture-source", "original"))
    with sqlite3.connect(store.path) as conn:
        conn.execute(
            "UPDATE memories SET revision=? WHERE memory_id=?",
            (MAX, item.memory_id),
        )
    with pytest.raises(MemoryConflictError, match="exhausted"):
        store.put(
            MemoryWrite(scope, "fixture-source", "replacement"),
            expected_revision=MAX,
        )
    with sqlite3.connect(store.path) as conn:
        assert conn.execute(
            "SELECT content,revision FROM memories WHERE memory_id=?",
            (item.memory_id,),
        ).fetchone() == ("original", MAX)
        assert conn.execute("SELECT COUNT(*) FROM memory_events").fetchone()[0] == 1


@pytest.mark.parametrize("cursor", [True, -1, MAX + 1, 1 << 80])
def test_invalid_event_cursor_rejected_without_sqlite_binding(tmp_path, cursor):
    store = SQLiteMemoryStore(tmp_path / "memory.db", clock_ms=lambda: 10)
    with pytest.raises(ValueError, match="after_event_id"):
        store.events(MemoryScope("fixture-owner"), after_event_id=cursor)


@pytest.mark.parametrize("revision", [True, -1, MAX + 1, 1 << 80])
def test_invalid_expected_revision_is_rejected(tmp_path, revision):
    store = SQLiteMemoryStore(tmp_path / "memory.db", clock_ms=lambda: 10)
    with pytest.raises(ValueError, match="expected_revision"):
        store.put(
            MemoryWrite(MemoryScope("fixture-owner"), "fixture-source", "text"),
            expected_revision=revision,
        )
