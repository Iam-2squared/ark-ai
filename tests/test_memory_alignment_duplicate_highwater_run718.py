"""Standalone local Memory alignment must reject duplicate SQLite sequence rows.

sqlite_sequence.name is not UNIQUE in SQLite. A fetchone() high-water check
would silently accept an extra forged marker. These are disposable databases,
not authenticated external proof or authorization.
"""

from __future__ import annotations

import sqlite3
from contextlib import closing

import pytest

from ark.memory import MemoryScope, MemoryWrite, SQLiteMemoryStore
from ark.memory.sqlite_event_alignment import (
    MemoryEventAlignmentRejected,
    review_memory_event_alignment,
)


def _store(tmp_path, *, populated: bool):
    store = SQLiteMemoryStore(tmp_path / "duplicate-sequence.sqlite", clock_ms=lambda: 99)
    if populated:
        store.put(MemoryWrite(MemoryScope("synthetic", "notes"), "one", "first"))
    return store


def _rows(path):
    with closing(sqlite3.connect(path)) as conn:
        return conn.execute(
            "SELECT name,seq FROM sqlite_sequence ORDER BY rowid"
        ).fetchall()


def test_duplicate_highwater_with_correct_first_row_is_denied(tmp_path):
    store = _store(tmp_path, populated=True)
    assert review_memory_event_alignment(store).event_count == 1
    with closing(sqlite3.connect(store.path)) as conn, conn:
        conn.execute(
            "INSERT INTO sqlite_sequence(name,seq) VALUES('memory_events', 100)"
        )
    before = _rows(store.path)
    assert [row for row in before if row[0] == "memory_events"] == [
        ("memory_events", 1), ("memory_events", 100),
    ]
    with pytest.raises(MemoryEventAlignmentRejected, match="high-water"):
        review_memory_event_alignment(store)
    assert _rows(store.path) == before


def test_empty_history_duplicate_sequence_marker_fails_closed(tmp_path):
    store = _store(tmp_path, populated=False)
    assert review_memory_event_alignment(store).event_count == 0
    with closing(sqlite3.connect(store.path)) as conn, conn:
        conn.execute(
            "INSERT INTO sqlite_sequence(name,seq) VALUES('memory_events', 0)"
        )
        conn.execute(
            "INSERT INTO sqlite_sequence(name,seq) VALUES('memory_events', 0)"
        )
    with pytest.raises(MemoryEventAlignmentRejected, match="tail"):
        review_memory_event_alignment(store)


def test_other_owner_append_keeps_single_highwater_valid(tmp_path):
    store = _store(tmp_path, populated=True)
    store.put(MemoryWrite(MemoryScope("another-owner", "notes"), "two", "second"))
    report = review_memory_event_alignment(store)
    assert report.event_count == 2
    assert report.last_event_id == 2
    assert report.independently_authenticated is False
    assert report.action_authorized is False
    assert _rows(store.path) == [("memory_events", 2)]
