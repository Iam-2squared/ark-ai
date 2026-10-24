"""Review one Memory snapshot without silently switching source paths.

These tests use only local SQLite fixtures and cannot authorize use of
personal content, deletion, disclosure, or backend actions.
"""

from pathlib import Path

import pytest

import ark.memory.synthetic_multiscope_integrity_review as reviewer
from ark.memory.contracts import MemoryScope, MemoryWrite
from ark.memory.sqlite_store import SQLiteMemoryStore
from ark.memory.synthetic_multiscope_integrity_review import (
    SyntheticMemorySnapshotRejected,
    review_synthetic_memory_scopes,
)


def _state(tmp_path: Path):
    store = SQLiteMemoryStore(
        tmp_path / "multi-scope # %.sqlite", clock_ms=lambda: 100,
    )
    scopes = (
        MemoryScope("owner", "alpha"),
        MemoryScope("owner", "beta"),
    )
    for scope in scopes:
        store.put(MemoryWrite(scope, "fixture", "PRIVATE-LOCAL-CONTENT"))
    return store, scopes


def test_stable_source_object_produces_inert_snapshot(tmp_path: Path):
    store, scopes = _state(tmp_path)
    receipt = review_synthetic_memory_scopes(store, scopes)
    assert [item.live_row_count for item in receipt.scopes] == [1, 1]
    assert receipt.context_use_authorized is False
    assert receipt.deletion_authorized is False
    assert receipt.external_disclosure_authorized is False
    assert "PRIVATE-LOCAL-CONTENT" not in repr(receipt)


@pytest.mark.parametrize("retained", [False, True])
def test_equal_value_new_path_object_during_hydration_is_denied(
    tmp_path: Path, monkeypatch, retained: bool,
):
    store, scopes = _state(tmp_path)
    saved = review_synthetic_memory_scopes(store, scopes)
    original_path = store.path
    original_record = reviewer._record
    seen = 0

    def swap_after_row(row):
        nonlocal seen
        record = original_record(row)
        seen += 1
        if seen == 1:
            store.path = Path(str(original_path))
            assert store.path == original_path
            assert store.path is not original_path
        return record

    monkeypatch.setattr(reviewer, "_record", swap_after_row)
    kwargs = {"require_same_snapshot": saved} if retained else {}
    with pytest.raises(SyntheticMemorySnapshotRejected, match="scope or source changed"):
        review_synthetic_memory_scopes(store, scopes, **kwargs)
    assert seen > 0
    assert original_path.exists()


def test_invalid_source_type_is_rejected_without_creating_file(tmp_path: Path):
    store, scopes = _state(tmp_path)
    original_path = store.path
    store.path = str(store.path)
    with pytest.raises(SyntheticMemorySnapshotRejected, match="retain a Path"):
        review_synthetic_memory_scopes(store, scopes)
    assert original_path.exists()


def test_different_path_after_first_row_is_rejected_without_opening_it(
    tmp_path: Path, monkeypatch,
):
    store, scopes = _state(tmp_path)
    other_path = tmp_path / "never-created.sqlite"
    original_record = reviewer._record

    def drift(row):
        record = original_record(row)
        store.path = other_path
        return record

    monkeypatch.setattr(reviewer, "_record", drift)
    with pytest.raises(SyntheticMemorySnapshotRejected, match="scope or source changed"):
        review_synthetic_memory_scopes(store, scopes)
    assert not other_path.exists()
