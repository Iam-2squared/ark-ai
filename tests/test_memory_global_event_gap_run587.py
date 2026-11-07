"""Memory v1 global event reconciliation refuses missing append-only IDs.

The fixtures are synthetic local SQLite, not authenticated deletion evidence.
"""

import sqlite3
from pathlib import Path

import pytest

from ark.memory.contracts import MemoryScope, MemoryWrite
from ark.memory.sqlite_event_alignment import (
    MemoryEventAlignmentRejected,
    review_memory_event_alignment,
)
from ark.memory.sqlite_store import SQLiteMemoryStore


def _history(tmp_path: Path) -> SQLiteMemoryStore:
    store = SQLiteMemoryStore(tmp_path / "memory.sqlite", clock_ms=lambda: 100)
    for index in range(3):
        store.put(
            MemoryWrite(MemoryScope("fixture-owner"), f"fixture-{index}", f"value-{index}")
        )
    return store


@pytest.mark.parametrize("missing_event", (1, 2))
def test_reconciler_rejects_missing_first_or_middle_global_event(
    tmp_path: Path, missing_event: int,
):
    store = _history(tmp_path)
    with sqlite3.connect(store.path) as conn:
        memory_id = conn.execute(
            "SELECT memory_id FROM memory_events WHERE event_id=?",
            (missing_event,),
        ).fetchone()[0]
        # A matching deletion of both the row and its event used to look
        # like an internally coherent two-memory history without a witness.
        conn.execute("DELETE FROM memories WHERE memory_id=?", (memory_id,))
        conn.execute("DELETE FROM memory_events WHERE event_id=?", (missing_event,))
        preserved = conn.execute(
            "SELECT event_id FROM memory_events ORDER BY event_id"
        ).fetchall()
    assert len(preserved) == 2
    with pytest.raises(MemoryEventAlignmentRejected, match="event ID gap"):
        review_memory_event_alignment(store)
    with sqlite3.connect(store.path) as conn:
        assert conn.execute(
            "SELECT event_id FROM memory_events ORDER BY event_id"
        ).fetchall() == preserved


def test_event_id_jump_is_not_an_append_only_history(tmp_path: Path):
    store = _history(tmp_path)
    with sqlite3.connect(store.path) as conn:
        conn.execute("UPDATE memory_events SET event_id=20 WHERE event_id=3")
    with pytest.raises(MemoryEventAlignmentRejected, match="event ID gap"):
        review_memory_event_alignment(store)


def test_normal_multi_scope_history_still_reconciles(tmp_path: Path):
    store = _history(tmp_path)
    initial = review_memory_event_alignment(store)
    assert (initial.row_count, initial.event_count, initial.last_event_id) == (3, 3, 3)
    restarted = SQLiteMemoryStore(store.path, clock_ms=lambda: 101)
    restarted.put(MemoryWrite(MemoryScope("another-owner"), "new", "new value"))
    later = review_memory_event_alignment(restarted)
    assert (later.row_count, later.event_count, later.last_event_id) == (4, 4, 4)
    assert later.digest != initial.digest
    assert later.action_authorized is False
    assert later.deletion_or_erasure_proven is False
