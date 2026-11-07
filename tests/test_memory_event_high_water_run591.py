"""Read-only Memory audit detects local missing suffix via AUTOINCREMENT.

The high-water mark is writable by a database owner and is *not* independent
evidence, authenticated provenance, consent, or proof of erasure.
"""

import sqlite3

import pytest

from ark.memory.contracts import MemoryScope, MemoryWrite
from ark.memory.sqlite_event_alignment import (
    MemoryEventAlignmentRejected,
    review_memory_event_alignment,
)
from ark.memory.sqlite_store import SQLiteMemoryStore


def _history(tmp_path):
    store = SQLiteMemoryStore(tmp_path / "memory.sqlite", clock_ms=lambda: 300)
    for n in (1, 2, 3):
        store.put(MemoryWrite(MemoryScope("local-user"), f"src-{n}", f"value-{n}"))
    return store


def _database_snapshot(path):
    with sqlite3.connect(path) as conn:
        return (
            conn.execute(
                "SELECT memory_id FROM memories ORDER BY memory_id"
            ).fetchall(),
            conn.execute(
                "SELECT event_id FROM memory_events ORDER BY event_id"
            ).fetchall(),
            conn.execute(
                "SELECT seq FROM sqlite_sequence WHERE name='memory_events'"
            ).fetchall(),
        )


@pytest.mark.parametrize("delete_everything", (False, True))
def test_closed_history_with_missing_tail_is_rejected_without_modifying_db(
    tmp_path, delete_everything,
):
    store = _history(tmp_path)
    with sqlite3.connect(store.path) as conn:
        if delete_everything:
            conn.execute("DELETE FROM memories")
            conn.execute("DELETE FROM memory_events")
        else:
            terminal_id = conn.execute(
                "SELECT memory_id FROM memory_events WHERE event_id=3"
            ).fetchone()[0]
            conn.execute("DELETE FROM memories WHERE memory_id=?", (terminal_id,))
            conn.execute("DELETE FROM memory_events WHERE event_id=3")
    before = _database_snapshot(store.path)
    assert before[2] == [(3,)]
    with pytest.raises(MemoryEventAlignmentRejected, match="event tail|high-water"):
        review_memory_event_alignment(store)
    assert _database_snapshot(store.path) == before


def test_rewritten_sqlite_sequence_is_rejected_in_read_only_review(tmp_path):
    store = _history(tmp_path)
    with sqlite3.connect(store.path) as conn:
        conn.execute(
            "UPDATE sqlite_sequence SET seq=99 WHERE name='memory_events'"
        )
    before = _database_snapshot(store.path)
    with pytest.raises(MemoryEventAlignmentRejected, match="high-water"):
        review_memory_event_alignment(store)
    assert _database_snapshot(store.path) == before


def test_missing_high_water_row_is_rejected_for_nonempty_history(tmp_path):
    store = _history(tmp_path)
    with sqlite3.connect(store.path) as conn:
        conn.execute("DELETE FROM sqlite_sequence WHERE name='memory_events'")
    with pytest.raises(MemoryEventAlignmentRejected, match="high-water"):
        review_memory_event_alignment(store)


def test_normal_restart_and_delete_history_preserve_event_high_water(tmp_path):
    store = _history(tmp_path)
    snapshot = review_memory_event_alignment(store)
    assert (snapshot.row_count, snapshot.event_count, snapshot.last_event_id) == (3, 3, 3)
    restarted = SQLiteMemoryStore(store.path, clock_ms=lambda: 301)
    with sqlite3.connect(store.path) as conn:
        memory_id = conn.execute(
            "SELECT memory_id FROM memories ORDER BY memory_id LIMIT 1"
        ).fetchone()[0]
    assert restarted.delete(memory_id, MemoryScope("local-user"), expected_revision=1)
    reviewed = review_memory_event_alignment(restarted)
    assert (reviewed.row_count, reviewed.event_count, reviewed.last_event_id) == (2, 4, 4)
    assert reviewed.action_authorized is False
    assert reviewed.deletion_or_erasure_proven is False
