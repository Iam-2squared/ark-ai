"""Atomic multi-namespace Memory lifecycle and row-integrity review."""

import hashlib
import sqlite3
from pathlib import Path

import pytest

from ark.memory.contracts import MemoryScope, MemoryWrite
from ark.memory.sqlite_store import SQLiteMemoryStore
from ark.memory.synthetic_event_continuity_review import (
    SyntheticMemoryEventRejected,
    review_synthetic_memory_event_continuity,
)
from ark.memory.synthetic_multiscope_integrity_review import (
    SyntheticMemorySnapshotRejected,
    review_synthetic_memory_scopes,
)


def _fixture(tmp_path: Path, *, clock=None):
    store = SQLiteMemoryStore(
        tmp_path / "Memory # %.sqlite",
        clock_ms=clock or (lambda: 100),
    )
    scopes = (MemoryScope("PRIVATE-OWNER-IDENTITY", "alpha"), MemoryScope("PRIVATE-OWNER-IDENTITY", "beta"))
    return store, scopes


def _write(store, scope, text, *, revision=0, expiry=None):
    return store.put(
        MemoryWrite(scope, "source", text, expires_at_ms=expiry),
        expected_revision=revision,
    )


def _review(state, **kwargs):
    return review_synthetic_memory_scopes(state[0], state[1], **kwargs)


def test_empty_multi_scope_snapshot_is_inert_and_metadata_only(tmp_path: Path):
    state = _fixture(tmp_path)
    result = _review(state)
    assert len(result.scopes) == 2
    assert all(item.events.event_count == 0 for item in result.scopes)
    assert result.context_use_authorized is False
    assert result.deletion_authorized is False
    assert result.external_disclosure_authorized is False
    assert "PRIVATE-OWNER-IDENTITY" not in repr(result)
    assert "alpha" not in repr(result)


def test_interleaved_global_events_belong_to_exact_scopes(tmp_path: Path):
    store, scopes = state = _fixture(tmp_path)
    _write(store, scopes[0], "PRIVATE-ALPHA")
    _write(store, scopes[1], "PRIVATE-BETA")
    _write(store, scopes[0], "PRIVATE-ALPHA-UPDATE", revision=1)
    observed = _review(state)
    assert [entry.events.event_count for entry in observed.scopes] == [2, 1]
    assert [entry.events.last_event_id for entry in observed.scopes] == [3, 2]
    assert [entry.live_row_count for entry in observed.scopes] == [1, 1]
    assert "PRIVATE" not in repr(observed)


def test_single_scope_witness_is_compatible_with_multiscope_prefix(tmp_path: Path):
    store, scopes = state = _fixture(tmp_path)
    _write(store, scopes[0], "SECRET-A")
    _write(store, scopes[1], "SECRET-B")
    prior = tuple(
        review_synthetic_memory_event_continuity(store, scope) for scope in scopes
    )
    _write(store, scopes[1], "SECRET-B2", revision=1)
    snapshot = _review(state, retained_events=prior)
    assert [value.events.event_count for value in snapshot.scopes] == [1, 2]


def test_retained_exact_snapshot_rejects_even_legitimate_cas_advance(tmp_path: Path):
    store, scopes = state = _fixture(tmp_path)
    _write(store, scopes[0], "SECRET-A")
    original = _review(state)
    _write(store, scopes[0], "SECRET-B", revision=1)
    assert _review(state).snapshot_digest != original.snapshot_digest
    with pytest.raises(SyntheticMemorySnapshotRejected, match="snapshot changed"):
        _review(state, require_same_snapshot=original)
    assert _review(state, retained_events=tuple(
        item.events for item in original.scopes
    )).scopes[0].events.event_count == 2


def test_same_revision_coherent_content_rewrite_requires_new_review(tmp_path: Path):
    store, scopes = state = _fixture(tmp_path)
    record = _write(store, scopes[0], "PRIVATE-ORIGINAL")
    old = _review(state)
    changed = "PRIVATE-REWRITTEN"
    with sqlite3.connect(store.path) as conn:
        conn.execute(
            "UPDATE memories SET content=?,content_sha256=? WHERE memory_id=?",
            (changed, hashlib.sha256(changed.encode()).hexdigest(), record.memory_id),
        )
    # Event-chain metadata alone cannot authenticate historical row content.
    assert _review(state, retained_events=tuple(
        item.events for item in old.scopes
    )).snapshot_digest != old.snapshot_digest
    with pytest.raises(SyntheticMemorySnapshotRejected, match="snapshot changed"):
        _review(state, require_same_snapshot=old)


def test_live_revision_drift_without_event_is_rejected(tmp_path: Path):
    store, scopes = state = _fixture(tmp_path)
    _write(store, scopes[0], "PRIVATE")
    with sqlite3.connect(store.path) as conn:
        conn.execute("UPDATE memories SET revision=8")
    with pytest.raises(SyntheticMemorySnapshotRejected, match="live rows"):
        _review(state)


def test_invalid_event_history_is_rejected(tmp_path: Path):
    store, scopes = state = _fixture(tmp_path)
    _write(store, scopes[0], "PRIVATE")
    with sqlite3.connect(store.path) as conn:
        conn.execute("UPDATE memory_events SET operation='update'")
    with pytest.raises(SyntheticMemorySnapshotRejected, match="update transition"):
        _review(state)


def test_delete_and_recreate_same_id_are_distinct_lifecycles(tmp_path: Path):
    store, scopes = state = _fixture(tmp_path)
    row = _write(store, scopes[0], "PRIVATE-FIRST")
    assert store.delete(row.memory_id, scopes[0], expected_revision=1)
    _write(store, scopes[0], "PRIVATE-SECOND")
    observed = _review(state)
    assert observed.scopes[0].events.event_count == 3
    assert observed.scopes[0].live_row_count == 1


def test_expiry_event_reconciles_with_empty_live_scope(tmp_path: Path):
    clock = [100]
    store, scopes = state = _fixture(tmp_path, clock=lambda: clock[0])
    _write(store, scopes[0], "PRIVATE-EXPIRING", expiry=120)
    clock[0] = 121
    assert store.purge_expired(scope=scopes[0]) == 1
    observed = _review(state)
    assert observed.scopes[0].events.event_count == 2
    assert observed.scopes[0].live_row_count == 0


@pytest.mark.parametrize("invalid", [
    [], (), (MemoryScope("owner", "one"),) * 2,
    (MemoryScope("owner", "one"), MemoryScope("other", "two")),
    (MemoryScope("owner", "one"), object()),
])
def test_invalid_scope_collections_fail_closed(tmp_path: Path, invalid):
    store, _scopes = _fixture(tmp_path)
    with pytest.raises(SyntheticMemorySnapshotRejected, match="exact|distinct"):
        review_synthetic_memory_scopes(store, invalid)


def test_changed_retained_epoch_is_rejected(tmp_path: Path):
    state = _fixture(tmp_path)
    first = _review(state)
    witness = first.scopes[0].events
    object.__setattr__(witness, "event_count", True)
    with pytest.raises(SyntheticMemoryEventRejected, match="invalid"):
        _review(state, retained_events=(witness, first.scopes[1].events))


def test_invalid_retained_snapshot_type_is_rejected(tmp_path: Path):
    state = _fixture(tmp_path)
    with pytest.raises(SyntheticMemorySnapshotRejected, match="exact retained"):
        _review(state, require_same_snapshot=object())


def test_schema_drift_after_initialization_is_rejected(tmp_path: Path):
    store, _scopes = state = _fixture(tmp_path)
    with sqlite3.connect(store.path) as conn:
        conn.execute("PRAGMA user_version=2")
    with pytest.raises(RuntimeError, match="schema"):
        _review(state)


def test_missing_sqlite_file_is_not_recreated(tmp_path: Path):
    store, _scopes = state = _fixture(tmp_path)
    _write(store, state[1][0], "PRIVATE")
    path = store.path
    path.rename(tmp_path / "moved.sqlite")
    with pytest.raises((RuntimeError, sqlite3.Error)):
        _review(state)
    assert not path.exists()
