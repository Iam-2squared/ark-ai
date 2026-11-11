"""Scoped offline Memory snapshots also require a coherent global event tip.

Corruption edits below touch disposable SQLite fixtures, never user Memory.
Global high-water cannot authenticate foreign payloads or retained history.
"""

import sqlite3

import pytest

from ark.memory.contracts import MemoryScope, MemoryWrite
from ark.memory.sqlite_store import SQLiteMemoryStore
from ark.memory.synthetic_multiscope_integrity_review import (
    SyntheticMemorySnapshotRejected,
    review_synthetic_memory_scopes,
)


def _prepare(tmp_path):
    store = SQLiteMemoryStore(tmp_path / "scoped-global-tip.sqlite",
                              clock_ms=lambda: 1000)
    target = MemoryScope("scope-owner", "chosen")
    foreign = MemoryScope("other-owner", "different")
    first = store.put(MemoryWrite(target, "first", "private first"))
    other = store.put(MemoryWrite(foreign, "foreign", "private foreign"))
    return store, target, foreign, first, other


@pytest.mark.parametrize("delete_position", ["tail", "middle"])
def test_unselected_owner_history_cannot_disappear(tmp_path, delete_position):
    store, target, _, _, other = _prepare(tmp_path)
    if delete_position == "middle":
        store.put(MemoryWrite(target, "second", "private second"))
    with sqlite3.connect(store.path) as conn:
        conn.execute("DELETE FROM memories WHERE memory_id=?", (other.memory_id,))
        conn.execute("DELETE FROM memory_events WHERE memory_id=?", (other.memory_id,))
    with pytest.raises(SyntheticMemorySnapshotRejected, match="global.*high-water"):
        review_synthetic_memory_scopes(store, (target,))


def test_duplicate_global_highwater_marker_is_not_ignored(tmp_path):
    store, target, _, _, _ = _prepare(tmp_path)
    with sqlite3.connect(store.path) as conn:
        conn.execute(
            "INSERT INTO sqlite_sequence(name,seq) VALUES ('memory_events',2)"
        )
    with pytest.raises(SyntheticMemorySnapshotRejected, match="global.*high-water"):
        review_synthetic_memory_scopes(store, (target,))


def test_normal_unselected_owner_append_does_not_break_scoped_review(tmp_path):
    store, target, foreign, _, _ = _prepare(tmp_path)
    initial = review_synthetic_memory_scopes(store, (target,))
    store.put(MemoryWrite(foreign, "second", "another private row"))
    after = review_synthetic_memory_scopes(store, (target,))
    assert after.snapshot_digest == initial.snapshot_digest
    assert after.scopes[0].events.event_count == 1
    assert after.context_use_authorized is False
    assert after.external_disclosure_authorized is False
