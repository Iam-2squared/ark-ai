"""Memory v1 lexical search scan remains bounded and read-only."""

import sqlite3

import pytest

import ark.memory.sqlite_store as store_module
from ark.memory import (
    MemoryQuery,
    MemorySchemaError,
    MemoryScope,
    MemoryWrite,
    SQLiteMemoryStore,
)


def _store(tmp_path):
    return SQLiteMemoryStore(tmp_path / "memory.sqlite3", clock_ms=lambda: 100)


def _insert(store, namespace, count, *, expires=None):
    scope = MemoryScope("local-owner", namespace)
    for index in range(count):
        store.put(MemoryWrite(
            scope, f"source-{index}", f"fixture searchable {index}",
            expires_at_ms=expires,
        ))
    return scope


@pytest.mark.parametrize("text", ["", "fixture", "absent"])
@pytest.mark.parametrize("include_expired", [False, True])
def test_oversized_namespace_denied_before_full_hydration(
    tmp_path, monkeypatch, text, include_expired,
):
    store = _store(tmp_path)
    scope = _insert(store, "private", 3, expires=90)
    monkeypatch.setattr(store_module, "_MAX_NAMESPACE_SEARCH_ROWS", 2)
    with pytest.raises(MemorySchemaError, match="namespace scan budget"):
        store.search(MemoryQuery(
            scope, text, limit=1, include_expired=include_expired,
        ))
    # The rejection is a read-only resource fence, never automatic deletion.
    with sqlite3.connect(store.path) as conn:
        assert conn.execute("SELECT COUNT(*) FROM memories").fetchone() == (3,)


def test_exact_namespace_budget_preserves_deterministic_ranking(
    tmp_path, monkeypatch,
):
    store = _store(tmp_path)
    scope = _insert(store, "private", 2)
    monkeypatch.setattr(store_module, "_MAX_NAMESPACE_SEARCH_ROWS", 2)
    result = store.search(MemoryQuery(scope, "fixture", limit=2))
    assert [item.memory_id for item in result] == sorted(item.memory_id for item in result)
    assert {item.source_id for item in result} == {"source-0", "source-1"}
    assert all(item.scope == scope for item in result)


def test_other_owner_or_namespace_does_not_exhaust_scoped_budget(
    tmp_path, monkeypatch,
):
    store = _store(tmp_path)
    eligible = _insert(store, "selected", 2)
    _insert(store, "unrelated", 3)
    monkeypatch.setattr(store_module, "_MAX_NAMESPACE_SEARCH_ROWS", 2)
    assert len(store.search(MemoryQuery(eligible, limit=2))) == 2
    assert len(store.events(eligible)) == 2
