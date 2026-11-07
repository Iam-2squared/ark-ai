"""A bounded coherent Memory snapshot cannot hydrate arbitrary row counts.

Tests only use local SQLite fixtures and never read external personal data,
invoke an external model, or alter frozen Memory v1 DDL.
"""

import sqlite3
from pathlib import Path

import pytest

import ark.memory.coherent_snapshot_review as module
from ark.memory.contracts import MemorySchemaError, MemoryScope, MemoryWrite
from ark.memory.sqlite_store import SQLiteMemoryStore


def _store(tmp_path: Path) -> SQLiteMemoryStore:
    return SQLiteMemoryStore(tmp_path / "memory.sqlite", clock_ms=lambda: 100)


def _insert(store: SQLiteMemoryStore, namespace: str, count: int) -> None:
    scope = MemoryScope("fixture-owner", namespace)
    for ordinal in range(count):
        store.put(MemoryWrite(scope, f"source-{ordinal}", f"fixture text {ordinal}"))


@pytest.mark.parametrize("query", ("", "missing", "fixture"))
def test_oversized_namespace_denied_before_selection_or_return(
    tmp_path: Path, monkeypatch, query: str,
):
    store = _store(tmp_path)
    _insert(store, "private", 3)
    monkeypatch.setattr(module, "_MAX_NAMESPACE_SCAN_ROWS", 2)
    request = module.CoherentSnapshotRequest(
        "fixture-owner", ("private",), text=query, per_namespace_limit=1,
    )
    with pytest.raises(MemorySchemaError, match="row scan budget"):
        module.review_coherent_snapshot(store, request)

    # This is a read-only failure, not a purge or other privacy mutation.
    with sqlite3.connect(store.path) as conn:
        assert conn.execute("SELECT COUNT(*) FROM memories").fetchone() == (3,)


def test_exact_budget_accepts_ranked_read_without_dispatch(
    tmp_path: Path, monkeypatch,
):
    store = _store(tmp_path)
    _insert(store, "private", 2)
    monkeypatch.setattr(module, "_MAX_NAMESPACE_SCAN_ROWS", 2)
    result = module.review_coherent_snapshot(
        store, module.CoherentSnapshotRequest(
            "fixture-owner", ("private",), per_namespace_limit=2,
        ),
    )
    assert result.read_at_ms == 100
    assert len(result.records) == 1
    assert len(result.records[0]) == 2
    assert result.scopes[0].namespace == "private"
    assert len(result.provenance_sha256) == 64


def test_row_scan_budget_is_applied_per_namespace(
    tmp_path: Path, monkeypatch,
):
    store = _store(tmp_path)
    _insert(store, "first", 2)
    _insert(store, "second", 2)
    monkeypatch.setattr(module, "_MAX_NAMESPACE_SCAN_ROWS", 2)
    result = module.review_coherent_snapshot(
        store, module.CoherentSnapshotRequest(
            "fixture-owner", ("first", "second"), per_namespace_limit=2,
        ),
    )
    assert tuple(len(group) for group in result.records) == (2, 2)
