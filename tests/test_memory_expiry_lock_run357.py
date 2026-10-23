"""Expiry purge retains a writer lock and atomic content-free event receipt."""

import sqlite3
from contextlib import closing

import pytest

from ark.memory import MemoryScope, MemoryWrite, SQLiteMemoryStore


def test_expiry_clock_runs_after_writer_lock(tmp_path) -> None:
    path = tmp_path / "memory.sqlite3"
    state = {"probe": False}
    scope = MemoryScope("synthetic-person", "synthetic-privacy")

    def clock() -> int:
        if state["probe"]:
            # The expiry clock must run while the SQLite writer slot is held.
            with closing(sqlite3.connect(path, timeout=0.01)) as other:
                with pytest.raises(sqlite3.OperationalError, match="locked"):
                    other.execute("BEGIN IMMEDIATE")
        return 1000

    store = SQLiteMemoryStore(path, clock_ms=clock)
    record = store.put(MemoryWrite(scope, "fixture", "fixture", expires_at_ms=950))
    state["probe"] = True
    assert store.purge_expired(scope=scope) == 1
    state["probe"] = False
    assert store.get(record.memory_id, scope, include_expired=True) is None
    assert [event.operation for event in store.events(scope)] == ["create", "expire"]


def test_expiry_scope_and_cutoff_are_respected_without_extraneous_audit(tmp_path) -> None:
    store = SQLiteMemoryStore(tmp_path / "memory.sqlite3", clock_ms=lambda: 1000)
    left, right = MemoryScope("fixture-left"), MemoryScope("fixture-right")
    old_left = store.put(MemoryWrite(left, "old", "fixture", expires_at_ms=1000))
    new_left = store.put(MemoryWrite(left, "new", "fixture", expires_at_ms=1001))
    old_right = store.put(MemoryWrite(right, "old", "fixture", expires_at_ms=999))
    assert store.purge_expired(scope=left) == 1
    assert store.get(old_left.memory_id, left, include_expired=True) is None
    assert store.get(new_left.memory_id, left, include_expired=True) is not None
    assert store.get(old_right.memory_id, right, include_expired=True) is not None
    assert [event.operation for event in store.events(left)] == ["create", "create", "expire"]
    assert [event.operation for event in store.events(right)] == ["create"]
    assert store.purge_expired(scope=left) == 0
    assert [event.operation for event in store.events(left)].count("expire") == 1


def test_failed_expiry_audit_rolls_back_physical_deletion(tmp_path) -> None:
    path = tmp_path / "memory.sqlite3"
    store = SQLiteMemoryStore(path, clock_ms=lambda: 1000)
    scope = MemoryScope("fixture-person")
    old = store.put(MemoryWrite(scope, "temporary", "fixture", expires_at_ms=900))
    with sqlite3.connect(path) as conn:
        conn.execute("""CREATE TRIGGER synthetic_expire_audit_failure
            BEFORE INSERT ON memory_events
            WHEN NEW.operation='expire'
            BEGIN SELECT RAISE(ABORT, 'synthetic audit storage unavailable'); END""")
    with pytest.raises(sqlite3.DatabaseError, match="synthetic audit storage unavailable"):
        store.purge_expired(scope=scope)
    assert store.get(old.memory_id, scope, include_expired=True) is not None
    assert [event.operation for event in store.events(scope)] == ["create"]
