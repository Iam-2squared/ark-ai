"""Frozen Memory v1 mutators never recreate disappeared SQLite stores."""

import sqlite3
from pathlib import Path

import pytest

from ark.memory.contracts import MemoryScope, MemoryWrite
from ark.memory.sqlite_store import SQLiteMemoryStore


def _setup(tmp_path: Path):
    path = tmp_path / "Memory # %.sqlite"
    calls = []
    def clock():
        calls.append(100)
        return 100

    store = SQLiteMemoryStore(path, clock_ms=clock)
    scope = MemoryScope("fixture-owner", "fixture-namespace")
    item = store.put(MemoryWrite(scope, "source", "PRIVATE-ORIGINAL"))
    return store, scope, item, path, calls


@pytest.mark.parametrize("operation", ["put", "delete", "purge_scope", "purge_all"])
def test_missing_initialized_store_not_recreated_by_any_mutator(
    tmp_path: Path, operation: str,
):
    store, scope, item, path, calls = _setup(tmp_path)
    moved = tmp_path / "moved.sqlite"
    path.rename(moved)
    before_clocks = len(calls)
    with pytest.raises(sqlite3.OperationalError):
        if operation == "put":
            store.put(
                MemoryWrite(scope, "source", "PRIVATE-CHANGED"),
                expected_revision=1,
            )
        elif operation == "delete":
            store.delete(item.memory_id, scope, expected_revision=1)
        elif operation == "purge_scope":
            store.purge_expired(scope=scope)
        else:
            store.purge_expired()
    assert not path.exists()
    assert moved.exists()
    assert len(calls) == before_clocks


def test_restored_memory_preserves_cas_and_event_history(tmp_path: Path):
    store, scope, item, path, _clocks = _setup(tmp_path)
    backup = tmp_path / "restorable.sqlite"
    path.rename(backup)
    with pytest.raises(sqlite3.OperationalError):
        store.put(
            MemoryWrite(scope, "source", "PRIVATE-DENIED"),
            expected_revision=1,
        )
    backup.rename(path)
    record = store.put(
        MemoryWrite(scope, "source", "PRIVATE-RESTORED"),
        expected_revision=1,
    )
    assert record.memory_id == item.memory_id
    assert record.revision == 2
    assert [event.operation for event in store.events(scope)] == [
        "create", "update",
    ]


def test_explicit_bootstrap_still_creates_a_new_frozen_v1_database(tmp_path: Path):
    path = tmp_path / "fresh # %.sqlite"
    assert not path.exists()
    store = SQLiteMemoryStore(path, clock_ms=lambda: 100)
    assert path.exists()
    with sqlite3.connect(path) as conn:
        assert conn.execute("PRAGMA user_version").fetchone()[0] == 1
        assert conn.execute("PRAGMA journal_mode").fetchone()[0] == "wal"
    scope = MemoryScope("private-owner", "scope")
    record = store.put(MemoryWrite(scope, "source", "PRIVATE-FIXTURE"))
    assert store.get(record.memory_id, scope) == record


def test_runtime_path_retarget_to_missing_store_is_not_created(tmp_path: Path):
    store, scope, _item, old_path, calls = _setup(tmp_path)
    missing = tmp_path / "missing # %.sqlite"
    store.path = missing
    before = len(calls)
    with pytest.raises(sqlite3.OperationalError):
        store.put(MemoryWrite(scope, "new", "PRIVATE-UNSAVED"))
    assert not missing.exists()
    assert old_path.exists()
    assert len(calls) == before
