"""Initialized Memory reads cannot recreate a missing SQLite evidence file."""

import sqlite3
from contextlib import closing
from pathlib import Path

import pytest

from ark.memory.contracts import MemoryQuery, MemoryScope, MemoryWrite
from ark.memory.sqlite_store import SQLiteMemoryStore


def _prepared(path: Path):
    store = SQLiteMemoryStore(path, clock_ms=lambda: 42)
    scope = MemoryScope("fixture-user", "private")
    record = store.put(MemoryWrite(scope, "source", "alpha text", {"purpose": "test"}))
    return store, scope, record


@pytest.mark.parametrize("operation", ["get", "search", "events"])
def test_read_methods_never_create_replacement_database(tmp_path: Path, operation):
    path = tmp_path / "fixture.sqlite"
    store, scope, record = _prepared(path)
    path.rename(tmp_path / "preserved.sqlite")
    assert not path.exists()

    with pytest.raises(sqlite3.OperationalError):
        if operation == "get":
            store.get(record.memory_id, scope)
        elif operation == "search":
            store.search(MemoryQuery(scope, "alpha"))
        else:
            store.events(scope)
    assert not path.exists()


def test_uri_reserved_characters_read_correctly(tmp_path: Path):
    path = tmp_path / "fixture #1 %.sqlite"
    store, scope, record = _prepared(path)
    assert store.get(record.memory_id, scope).content == "alpha text"
    assert [item.memory_id for item in store.search(MemoryQuery(scope, "alpha"))] == [
        record.memory_id,
    ]
    assert store.events(scope)[0].memory_id == record.memory_id


def test_read_connection_refuses_fixture_mutation(tmp_path: Path):
    store, scope, record = _prepared(tmp_path / "fixture.sqlite")
    with closing(store._connect_readonly()) as conn:
        with pytest.raises(sqlite3.OperationalError, match="readonly"):
            conn.execute("DELETE FROM memories")
    assert store.get(record.memory_id, scope) is not None


def test_readonly_snapshot_does_not_allow_scope_leakage(tmp_path: Path):
    store, scope, record = _prepared(tmp_path / "fixture.sqlite")
    other = MemoryScope("other-user", scope.namespace)
    assert store.get(record.memory_id, other) is None
    assert store.search(MemoryQuery(other)) == []
    assert store.events(other) == []
