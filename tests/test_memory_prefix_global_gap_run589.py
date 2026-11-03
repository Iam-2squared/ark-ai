"""Global v1 event-ID gaps fail closed in retained Memory prefix review.

The synthetic SQLite fixture is not authenticated historical evidence, and
these checks cannot detect whole-database replacement or unanchored truncation.
"""

import sqlite3
from pathlib import Path

import pytest

from ark.memory.contracts import MemoryScope, MemoryWrite
from ark.memory.sqlite_event_prefix_review import (
    MemoryEventPrefixRejected,
    capture_local_memory_event_prefix,
    compare_local_memory_event_prefix,
)
from ark.memory.sqlite_store import SQLiteMemoryStore


def _store(tmp_path: Path) -> SQLiteMemoryStore:
    store = SQLiteMemoryStore(tmp_path / "prefix-gap.sqlite", clock_ms=lambda: 100)
    scope = MemoryScope("fixture-owner")
    for index in range(3):
        store.put(MemoryWrite(scope, f"source-{index}", f"private-{index}"))
    return store


@pytest.mark.parametrize("lost_id", (1, 2))
def test_capture_rejects_missing_genesis_or_middle_event(tmp_path: Path, lost_id: int):
    store = _store(tmp_path)
    with sqlite3.connect(store.path) as conn:
        conn.execute("DELETE FROM memory_events WHERE event_id=?", (lost_id,))
        remaining = conn.execute(
            "SELECT event_id FROM memory_events ORDER BY event_id"
        ).fetchall()
    with pytest.raises(MemoryEventPrefixRejected, match="event ID gap"):
        capture_local_memory_event_prefix(store)
    with sqlite3.connect(store.path) as conn:
        assert conn.execute(
            "SELECT event_id FROM memory_events ORDER BY event_id"
        ).fetchall() == remaining


def test_retained_prefix_does_not_hide_gap_in_new_events(tmp_path: Path):
    store = SQLiteMemoryStore(tmp_path / "advanced.db", clock_ms=lambda: 100)
    scope = MemoryScope("fixture-owner")
    store.put(MemoryWrite(scope, "one", "private-one"))
    retained = capture_local_memory_event_prefix(store)
    store.put(MemoryWrite(scope, "two", "private-two"))
    store.put(MemoryWrite(scope, "three", "private-three"))
    with sqlite3.connect(store.path) as conn:
        conn.execute("DELETE FROM memory_events WHERE event_id=2")
    # The original prefix remains byte-for-byte valid, but the newer
    # append-only suffix has a missing event and cannot be trusted.
    with pytest.raises(MemoryEventPrefixRejected, match="event ID gap"):
        compare_local_memory_event_prefix(store, retained)


def test_overwritten_event_id_jump_is_not_accepted(tmp_path: Path):
    store = _store(tmp_path)
    with sqlite3.connect(store.path) as conn:
        conn.execute("UPDATE memory_events SET event_id=20 WHERE event_id=3")
    with pytest.raises(MemoryEventPrefixRejected, match="event ID gap"):
        capture_local_memory_event_prefix(store)


def test_normal_multiscope_append_retains_exact_prefix(tmp_path: Path):
    store = _store(tmp_path)
    retained = capture_local_memory_event_prefix(store)
    assert (retained.event_count, retained.last_event_id) == (3, 3)
    restarted = SQLiteMemoryStore(store.path, clock_ms=lambda: 101)
    restarted.put(MemoryWrite(MemoryScope("another-owner"), "four", "private-four"))
    result = compare_local_memory_event_prefix(restarted, retained)
    assert (result.previous_event_count, result.current_event_count) == (3, 4)
    assert result.status == "ADVANCED_PREFIX_UNAUTHENTICATED"
    assert result.action_authorized is False
