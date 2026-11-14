"""SQLite Memory source epochs cover zero-row reads and rollback paths."""

from pathlib import Path

import pytest

from ark.memory.contracts import MemoryQuery, MemorySchemaError, MemoryScope, MemoryWrite
from ark.memory.sqlite_store import SQLiteMemoryStore


def _store(tmp_path: Path) -> tuple[SQLiteMemoryStore, MemoryScope]:
    store = SQLiteMemoryStore(tmp_path / "memory.sqlite", clock_ms=lambda: 10)
    return store, MemoryScope("local-owner")


def _retarget(store: SQLiteMemoryStore) -> int:
    # Even an equal-path replacement is a new reflected-input epoch.
    store.path = Path(str(store.path))
    return 10


@pytest.mark.parametrize("populated", [False, True])
def test_search_rejects_retained_source_swap_during_clock(tmp_path: Path, populated: bool):
    store, scope = _store(tmp_path)
    if populated:
        store.put(MemoryWrite(scope, "source", "a stored phrase"))
    store._clock_ms = lambda: _retarget(store)
    with pytest.raises(MemorySchemaError, match="search source changed"):
        store.search(MemoryQuery(scope, "stored"))
    fresh = SQLiteMemoryStore(tmp_path / "memory.sqlite", clock_ms=lambda: 10)
    assert len(fresh.search(MemoryQuery(scope))) == int(populated)


def test_put_rolls_back_when_clock_retargets_source(tmp_path: Path):
    store, scope = _store(tmp_path)
    store._clock_ms = lambda: _retarget(store)
    with pytest.raises(MemorySchemaError, match="put source changed"):
        store.put(MemoryWrite(scope, "first", "private fixture"))
    fresh = SQLiteMemoryStore(tmp_path / "memory.sqlite", clock_ms=lambda: 10)
    assert fresh.search(MemoryQuery(scope)) == []
    assert fresh.events(scope) == []


def test_put_rolls_back_when_event_hook_retargets_source(tmp_path: Path, monkeypatch):
    store, scope = _store(tmp_path)
    original = store._event

    def injected(*args):
        original(*args)
        _retarget(store)

    monkeypatch.setattr(store, "_event", injected)
    with pytest.raises(MemorySchemaError, match="put source changed"):
        store.put(MemoryWrite(scope, "first", "private fixture"))
    fresh = SQLiteMemoryStore(tmp_path / "memory.sqlite", clock_ms=lambda: 10)
    assert fresh.search(MemoryQuery(scope)) == []
    assert fresh.events(scope) == []


def test_missing_delete_rejects_source_swap_during_clock(tmp_path: Path):
    store, scope = _store(tmp_path)
    store._clock_ms = lambda: _retarget(store)
    missing = "mem_" + "0" * 64
    with pytest.raises(MemorySchemaError, match="delete source changed"):
        store.delete(missing, scope, expected_revision=1)


def test_delete_rolls_back_on_source_swap_after_event(tmp_path: Path, monkeypatch):
    store, scope = _store(tmp_path)
    saved = store.put(MemoryWrite(scope, "first", "private fixture"))
    original = store._event

    def injected(*args):
        original(*args)
        _retarget(store)

    monkeypatch.setattr(store, "_event", injected)
    with pytest.raises(MemorySchemaError, match="delete source changed"):
        store.delete(saved.memory_id, scope, expected_revision=1)
    fresh = SQLiteMemoryStore(tmp_path / "memory.sqlite", clock_ms=lambda: 10)
    assert fresh.get(saved.memory_id, scope) is not None
    assert [event.operation for event in fresh.events(scope)] == ["create"]


def test_zero_expiry_purge_rejects_source_swap_during_clock(tmp_path: Path):
    store, scope = _store(tmp_path)
    store._clock_ms = lambda: _retarget(store)
    with pytest.raises(MemorySchemaError, match="purge source changed"):
        store.purge_expired(scope=scope)


def test_expiry_purge_rolls_back_after_source_swap(tmp_path: Path, monkeypatch):
    store, scope = _store(tmp_path)
    saved = store.put(MemoryWrite(scope, "first", "private fixture", expires_at_ms=5))
    original = store._event

    def injected(*args):
        original(*args)
        _retarget(store)

    monkeypatch.setattr(store, "_event", injected)
    with pytest.raises(MemorySchemaError, match="purge source changed"):
        store.purge_expired(scope=scope)
    fresh = SQLiteMemoryStore(tmp_path / "memory.sqlite", clock_ms=lambda: 10)
    assert fresh.get(saved.memory_id, scope, include_expired=True) is not None
    assert [event.operation for event in fresh.events(scope)] == ["create"]


def test_normal_cas_and_expiry_are_unchanged(tmp_path: Path):
    store, scope = _store(tmp_path)
    first = store.put(MemoryWrite(scope, "first", "one"))
    second = store.put(MemoryWrite(scope, "first", "two"), expected_revision=1)
    assert (first.revision, second.revision) == (1, 2)
    assert store.delete(second.memory_id, scope, expected_revision=2)
    assert store.get(second.memory_id, scope) is None
    assert [event.operation for event in store.events(scope)] == ["create", "update", "delete"]
