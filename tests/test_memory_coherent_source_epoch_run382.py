"""Read-only coherent Memory snapshots must not change source identity."""

from pathlib import Path

import pytest

import ark.memory.coherent_snapshot_review as snapshot_module
from ark.memory.coherent_snapshot_review import (
    CoherentSnapshotRequest,
    review_coherent_snapshot,
)
from ark.memory.contracts import MemorySchemaError, MemoryScope, MemoryWrite
from ark.memory.sqlite_store import SQLiteMemoryStore


def _setup(tmp_path: Path):
    store = SQLiteMemoryStore(
        tmp_path / "original # %.sqlite", clock_ms=lambda: 100,
    )
    scope = MemoryScope("offline-owner", "local")
    item = store.put(MemoryWrite(scope, "source", "SECRET-FIXTURE"))
    request = CoherentSnapshotRequest(scope.owner_id, (scope.namespace,))
    return store, scope, item, request


def test_unchanged_source_is_accepted_without_side_effects(tmp_path: Path):
    store, _, item, request = _setup(tmp_path)
    result = review_coherent_snapshot(store, request)
    assert result.records[0][0].memory_id == item.memory_id
    assert result.read_at_ms == 100
    assert store.path.exists()


def test_clock_callback_redirect_to_different_sqlite_rejected(tmp_path: Path):
    store, scope, _, request = _setup(tmp_path)
    alternative = SQLiteMemoryStore(tmp_path / "unrelated.sqlite")
    before = store.path
    store._clock_ms = lambda: setattr(store, "path", alternative.path) or 101
    with pytest.raises(MemorySchemaError, match="source path changed"):
        review_coherent_snapshot(store, request)
    assert alternative.search(
        __import__("ark.memory.contracts", fromlist=["MemoryQuery"]).MemoryQuery(scope)
    ) == []
    assert before.exists()


def test_clock_callback_same_value_different_path_object_rejected(tmp_path: Path):
    store, _, _, request = _setup(tmp_path)
    original = store.path
    store._clock_ms = lambda: setattr(store, "path", Path(str(original))) or 101
    with pytest.raises(MemorySchemaError, match="source path changed"):
        review_coherent_snapshot(store, request)
    assert original.exists()


def test_clock_callback_changes_source_type_rejected(tmp_path: Path):
    store, _, _, request = _setup(tmp_path)
    store._clock_ms = lambda: setattr(store, "path", "not-a-path") or 101
    with pytest.raises(MemorySchemaError, match="source path changed"):
        review_coherent_snapshot(store, request)


def test_wrong_source_type_rejected_before_database_access(tmp_path: Path):
    store, _, _, request = _setup(tmp_path)
    store.path = str(store.path)
    with pytest.raises(MemorySchemaError, match="stable Path"):
        review_coherent_snapshot(store, request)


def test_reflected_source_change_after_clock_during_row_hydration_rejected(
    tmp_path: Path, monkeypatch,
):
    store, _, _, request = _setup(tmp_path)
    first_path = store.path
    original_record = snapshot_module._record
    count = 0

    def change_source(row):
        nonlocal count
        result = original_record(row)
        count += 1
        if count == 1:
            store.path = tmp_path / "unrelated-source.sqlite"
        return result

    monkeypatch.setattr(snapshot_module, "_record", change_source)
    with pytest.raises(MemorySchemaError, match="source path changed"):
        review_coherent_snapshot(store, request)
    assert count == 1
    assert first_path.exists()
    assert not (tmp_path / "unrelated-source.sqlite").exists()


def test_missing_database_is_not_silently_recreated(tmp_path: Path):
    store, _, _, request = _setup(tmp_path)
    old_path = store.path
    old_path.rename(tmp_path / "moved.sqlite")
    with pytest.raises(MemorySchemaError, match="read-only"):
        review_coherent_snapshot(store, request)
    assert not old_path.exists()
