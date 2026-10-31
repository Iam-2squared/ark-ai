"""Exact cached Memory witness shape and concurrent-snapshot regression guards."""

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
    store = SQLiteMemoryStore(tmp_path / "scopes # %.sqlite", clock_ms=lambda: 100)
    scopes = (
        MemoryScope("PRIVATE-OWNER", "alpha"),
        MemoryScope("PRIVATE-OWNER", "beta"),
    )
    for namespace in scopes:
        store.put(MemoryWrite(namespace, "source", "PRIVATE-ORIGINAL"))
    return store, scopes


def test_unchanged_exact_snapshot_can_be_rechecked(tmp_path: Path):
    store, scopes = _state(tmp_path)
    previous = review_synthetic_memory_scopes(store, scopes)
    current = review_synthetic_memory_scopes(
        store, scopes, require_same_snapshot=previous,
    )
    assert current == previous
    assert current.context_use_authorized is False
    assert current.deletion_authorized is False


def test_bool_count_spoof_is_denied_even_though_python_bool_equals_one(tmp_path: Path):
    store, scopes = _state(tmp_path)
    previous = review_synthetic_memory_scopes(store, scopes)
    assert previous.scopes[0].live_row_count == 1
    object.__setattr__(previous.scopes[0], "live_row_count", True)
    with pytest.raises(SyntheticMemorySnapshotRejected, match="malformed cached Memory scope"):
        review_synthetic_memory_scopes(
            store, scopes, require_same_snapshot=previous,
        )


def test_late_nested_count_spoof_is_denied_after_row_hydration(
    tmp_path: Path, monkeypatch,
):
    store, scopes = _state(tmp_path)
    previous = review_synthetic_memory_scopes(store, scopes)
    original = reviewer._record
    fired = False

    def corrupt_after_shape_check(row):
        nonlocal fired
        result = original(row)
        if not fired:
            fired = True
            object.__setattr__(previous.scopes[0], "live_row_count", True)
        return result

    monkeypatch.setattr(reviewer, "_record", corrupt_after_shape_check)
    with pytest.raises(SyntheticMemorySnapshotRejected, match="malformed cached Memory scope"):
        review_synthetic_memory_scopes(
            store, scopes, require_same_snapshot=previous,
        )
    assert fired


def test_late_event_count_spoof_is_denied_after_row_hydration(
    tmp_path: Path, monkeypatch,
):
    store, scopes = _state(tmp_path)
    previous = review_synthetic_memory_scopes(store, scopes)
    original = reviewer._record
    fired = False

    def corrupt_after_shape_check(row):
        nonlocal fired
        result = original(row)
        if not fired:
            fired = True
            object.__setattr__(previous.scopes[0].events, "event_count", True)
        return result

    monkeypatch.setattr(reviewer, "_record", corrupt_after_shape_check)
    with pytest.raises(SyntheticMemorySnapshotRejected, match="malformed cached Memory event"):
        review_synthetic_memory_scopes(
            store, scopes, require_same_snapshot=previous,
        )


def test_retained_event_prefix_also_denies_late_bool_spoof(
    tmp_path: Path, monkeypatch,
):
    store, scopes = _state(tmp_path)
    previous = review_synthetic_memory_scopes(store, scopes)
    retained = tuple(scope.events for scope in previous.scopes)
    original = reviewer._record
    fired = False

    def corrupt_after_shape_check(row):
        nonlocal fired
        result = original(row)
        if not fired:
            fired = True
            object.__setattr__(retained[0], "event_count", True)
        return result

    monkeypatch.setattr(reviewer, "_record", corrupt_after_shape_check)
    with pytest.raises(RuntimeError, match="invalid retained"):
        review_synthetic_memory_scopes(
            store, scopes, retained_events=retained,
        )


def test_cached_owner_digest_reflective_swap_denied(tmp_path: Path):
    store, scopes = _state(tmp_path)
    previous = review_synthetic_memory_scopes(store, scopes)
    object.__setattr__(previous, "owner_digest", "memevt_" + "0" * 64)
    with pytest.raises(SyntheticMemorySnapshotRejected, match="malformed cached"):
        review_synthetic_memory_scopes(
            store, scopes, require_same_snapshot=previous,
        )


def test_second_namespace_write_during_first_row_read_cannot_mix_commits(
    tmp_path: Path, monkeypatch,
):
    store, scopes = _state(tmp_path)
    retained = review_synthetic_memory_scopes(store, scopes)
    writer = SQLiteMemoryStore(store.path, clock_ms=lambda: 101)
    original = reviewer._record
    wrote = False

    def write_during_hydration(row):
        nonlocal wrote
        result = original(row)
        if not wrote:
            wrote = True
            writer.put(
                MemoryWrite(scopes[1], "source", "PRIVATE-CHANGED"),
                expected_revision=1,
            )
        return result

    monkeypatch.setattr(reviewer, "_record", write_during_hydration)
    observed = review_synthetic_memory_scopes(
        store, scopes, require_same_snapshot=retained,
    )
    assert wrote
    assert observed == retained
    assert review_synthetic_memory_scopes(store, scopes) != retained
    with pytest.raises(SyntheticMemorySnapshotRejected, match="snapshot changed"):
        review_synthetic_memory_scopes(
            store, scopes, require_same_snapshot=retained,
        )


def test_reflectively_retargeted_scope_is_denied_after_read(
    tmp_path: Path, monkeypatch,
):
    store, scopes = _state(tmp_path)
    original = reviewer._record
    fired = False

    def retarget(row):
        nonlocal fired
        record = original(row)
        if not fired:
            fired = True
            object.__setattr__(scopes[0], "namespace", "different")
        return record

    monkeypatch.setattr(reviewer, "_record", retarget)
    with pytest.raises(SyntheticMemorySnapshotRejected, match="scope or source changed"):
        review_synthetic_memory_scopes(store, scopes)
