"""Append-only event prefix catches interior gaps and respects reincarnation.

These read-only diagnostics never authorize disclosure or external actions.
Only disposable local SQLite fixtures are touched.
"""

from __future__ import annotations

import sqlite3

import pytest

from ark.memory import MemoryScope, MemoryWrite, SQLiteMemoryStore
from ark.memory.sqlite_event_prefix_review import (
    MemoryEventPrefixRejected,
    capture_local_memory_event_prefix,
    compare_local_memory_event_prefix,
)


@pytest.mark.parametrize("removed_id", (1, 2))
def test_interior_event_gap_is_not_covered_by_later_valid_highwater(
    tmp_path, removed_id,
):
    store = SQLiteMemoryStore(tmp_path / "interior-gap.sqlite", clock_ms=lambda: 8000)
    scope = MemoryScope("owner", "private")
    store.put(MemoryWrite(scope, "first", "private first"))
    retained = capture_local_memory_event_prefix(store)
    store.put(MemoryWrite(scope, "second", "private second"))
    store.put(MemoryWrite(scope, "third", "private third"))
    with sqlite3.connect(store.path) as conn:
        # The local AUTOINCREMENT high-water still points at event #3,
        # but the journal is no longer an uninterrupted [1, 2, 3].
        conn.execute("DELETE FROM memory_events WHERE event_id=?", (removed_id,))
        sequence = conn.execute(
            "SELECT seq FROM sqlite_sequence WHERE name='memory_events'"
        ).fetchone()
        assert sequence == (3,)

    with pytest.raises(MemoryEventPrefixRejected):
        capture_local_memory_event_prefix(store)
    with pytest.raises(MemoryEventPrefixRejected):
        compare_local_memory_event_prefix(store, retained)


def test_delete_then_recreate_same_identity_is_new_lifecycle_not_authority(tmp_path):
    path = tmp_path / "reincarnation.sqlite"
    first = SQLiteMemoryStore(path, clock_ms=lambda: 8000)
    second = SQLiteMemoryStore(path, clock_ms=lambda: 9000)
    scope = MemoryScope("owner", "private")
    original = first.put(MemoryWrite(scope, "source", "private original"))
    retained = capture_local_memory_event_prefix(first)

    assert second.delete(original.memory_id, scope, expected_revision=1)
    recreated = second.put(
        MemoryWrite(scope, "source", "private replacement"),
        expected_revision=0,
    )
    assert recreated.memory_id == original.memory_id
    assert recreated.revision == 1
    tip = capture_local_memory_event_prefix(first)
    assert tip.event_count == tip.last_event_id == 3
    report = compare_local_memory_event_prefix(first, retained)
    assert report.previous_event_count == 1
    assert report.current_event_count == 3
    assert report.status == "ADVANCED_PREFIX_UNAUTHENTICATED"
    assert report.historical_writer_authenticated is False
    assert report.memory_disclosure_authorized is False
    assert report.action_authorized is False
    assert first.get(original.memory_id, scope).content == "private replacement"
