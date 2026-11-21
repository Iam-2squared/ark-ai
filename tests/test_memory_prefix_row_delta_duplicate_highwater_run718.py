"""Independent Memory event-prefix and row-delta scans deny duplicate tail markers.

SQLite's sqlite_sequence table does not require UNIQUE(name). One valid
first row must not hide a second, inconsistent AUTOINCREMENT marker.
"""

from __future__ import annotations

import sqlite3
from contextlib import closing

import pytest

from ark.memory import MemoryScope, MemoryWrite, SQLiteMemoryStore
from ark.memory.sqlite_event_prefix_review import (
    MemoryEventPrefixRejected,
    capture_local_memory_event_prefix,
    compare_local_memory_event_prefix,
)
from ark.memory.sqlite_retained_row_delta_review import (
    MemoryRowDeltaRejected,
    capture_local_memory_row_delta,
    review_retained_memory_row_delta,
)


def _setup(tmp_path, populated=True):
    store = SQLiteMemoryStore(tmp_path / "local-event-markers.sqlite", clock_ms=lambda: 77)
    if populated:
        store.put(MemoryWrite(MemoryScope("owner-a", "notes"), "one", "first"))
    prefix = capture_local_memory_event_prefix(store)
    rows = capture_local_memory_row_delta(store)
    return store, prefix, rows


def _insert_duplicate(store, value):
    with closing(sqlite3.connect(store.path)) as conn, conn:
        conn.execute(
            "INSERT INTO sqlite_sequence(name,seq) VALUES('memory_events', ?)",
            (value,),
        )


def test_prefix_and_row_delta_reject_duplicate_after_valid_first_marker(tmp_path):
    store, prefix, rows = _setup(tmp_path)
    # A normal second owner's append advances the retained witnesses.
    store.put(MemoryWrite(MemoryScope("owner-b", "notes"), "two", "second"))
    assert compare_local_memory_event_prefix(
        store, prefix,
    ).current_event_count == 2
    assert review_retained_memory_row_delta(store, rows).appended_events == 1
    _insert_duplicate(store, 55)
    with pytest.raises(MemoryEventPrefixRejected, match="high-water"):
        compare_local_memory_event_prefix(store, prefix)
    with pytest.raises(MemoryRowDeltaRejected, match="high-water"):
        review_retained_memory_row_delta(store, rows)


def test_empty_history_with_forged_sequence_is_rejected(tmp_path):
    store, prefix, rows = _setup(tmp_path, populated=False)
    assert capture_local_memory_event_prefix(store).event_count == 0
    _insert_duplicate(store, 0)
    with pytest.raises(MemoryEventPrefixRejected, match="high-water"):
        compare_local_memory_event_prefix(store, prefix)
    with pytest.raises(MemoryRowDeltaRejected, match="high-water"):
        review_retained_memory_row_delta(store, rows)


def test_normal_prefix_and_row_delta_preserve_deny_only_contract(tmp_path):
    store, prefix, rows = _setup(tmp_path)
    store.put(MemoryWrite(MemoryScope("owner-b", "notes"), "two", "second"))
    compared = compare_local_memory_event_prefix(store, prefix)
    reviewed = review_retained_memory_row_delta(store, rows)
    assert compared.current_event_count == 2
    assert compared.independent_witness_custody_proven is False
    assert compared.action_authorized is False
    assert reviewed.appended_events == 1
    assert reviewed.writer_authenticated is False
    assert reviewed.action_authorized is False
    assert reviewed.disclosure_authorized is False
