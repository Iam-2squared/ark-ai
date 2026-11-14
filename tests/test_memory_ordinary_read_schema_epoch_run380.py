"""Ordinary Memory read API must fail closed on post-startup schema edits."""

import sqlite3

import pytest

from ark.memory.contracts import MemoryQuery, MemorySchemaError, MemoryScope, MemoryWrite
from ark.memory.sqlite_store import SQLiteMemoryStore


def _fixture(tmp_path):
    store = SQLiteMemoryStore(
        tmp_path / "ordinary Memory # percent %.sqlite", clock_ms=lambda: 100,
    )
    scope = MemoryScope("owner", "private")
    saved = store.put(MemoryWrite(scope, "test", "PRIVATE user context"))
    return store, scope, saved


@pytest.mark.parametrize("tamper", [
    "PRAGMA user_version=2",
    "PRAGMA user_version=0",
    "DROP INDEX idx_mem_expiry",
    "ALTER TABLE memory_events ADD COLUMN injected TEXT",
    "CREATE TRIGGER unexpected AFTER INSERT ON memory_events BEGIN SELECT 1; END",
])
@pytest.mark.parametrize("read_api", ["get", "get_missing", "search", "events"])
def test_ordinary_reads_reject_schema_drift_after_startup(
    tmp_path, tamper, read_api,
):
    store, scope, saved = _fixture(tmp_path)
    with sqlite3.connect(store.path) as conn:
        conn.execute(tamper)

    with pytest.raises(MemorySchemaError, match="schema"):
        if read_api == "get":
            store.get(saved.memory_id, scope)
        elif read_api == "get_missing":
            store.get("mem_" + "0" * 64, scope)
        elif read_api == "search":
            store.search(MemoryQuery(scope, "no-match"))
        else:
            store.events(scope)


def test_valid_ordinary_read_functions_still_match_existing_contract(tmp_path):
    store, scope, saved = _fixture(tmp_path)
    assert store.get(saved.memory_id, scope) == saved
    assert store.get("mem_" + "0" * 64, scope) is None
    assert store.search(MemoryQuery(scope, "PRIVATE")) == [saved]
    assert [(item.operation, item.revision) for item in store.events(scope)] == [
        ("create", 1),
    ]


@pytest.mark.parametrize("method", ["get", "search", "events"])
def test_removed_memory_database_is_not_recreated_by_reads(tmp_path, method):
    store, scope, saved = _fixture(tmp_path)
    store.path.rename(tmp_path / "moved.sqlite")
    with pytest.raises(sqlite3.OperationalError):
        if method == "get":
            store.get(saved.memory_id, scope)
        elif method == "search":
            store.search(MemoryQuery(scope, "PRIVATE"))
        else:
            store.events(scope)
    assert not store.path.exists()
