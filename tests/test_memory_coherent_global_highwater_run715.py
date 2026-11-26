"""Cross-owner gaps and deleted tails are denied by ONE coherent WAL snapshot.

These deletions are deliberate disposable SQLite corruption fixtures. Local
AUTOINCREMENT high-water is not authenticated outside the database; a writer
capable of rewriting sqlite_sequence can still counterfeit local evidence.
"""

from __future__ import annotations

import sqlite3
from contextlib import closing

import pytest

from ark.memory import MemoryScope, MemoryWrite, SQLiteMemoryStore
from ark.memory.sqlite_event_alignment import review_memory_event_alignment
from ark.memory.sqlite_event_prefix_review import capture_local_memory_event_prefix
from ark.memory.sqlite_retained_coherent_review import (
    MemoryCoherentHistoryRejected,
    review_retained_coherent_memory,
)


def _case(tmp_path):
    store = SQLiteMemoryStore(tmp_path / "global-highwater.sqlite", clock_ms=lambda: 1000)
    first = store.put(MemoryWrite(MemoryScope("owner-a", "private"), "one", "first"))
    previous = (
        capture_local_memory_event_prefix(store),
        review_memory_event_alignment(store),
    )
    return store, first, previous


def _append(store, owner, source):
    return store.put(MemoryWrite(MemoryScope(owner, "private"), source, "synthetic"))


def _delete_row_and_event(store, record):
    with closing(sqlite3.connect(store.path)) as connection:
        with connection:
            connection.execute(
                "DELETE FROM memory_events WHERE memory_id=?", (record.memory_id,),
            )
            connection.execute(
                "DELETE FROM memories WHERE memory_id=?", (record.memory_id,),
            )


def test_missing_foreign_event_inside_new_suffix_is_not_safe_advance(tmp_path):
    store, _, retained = _case(tmp_path)
    missing = _append(store, "owner-b", "two")
    _append(store, "owner-c", "three")
    _delete_row_and_event(store, missing)
    with closing(sqlite3.connect(store.path)) as connection:
        assert connection.execute(
            "SELECT COUNT(*),MIN(event_id),MAX(event_id) FROM memory_events"
        ).fetchone() == (2, 1, 3)
    with pytest.raises(MemoryCoherentHistoryRejected, match="event ID gap"):
        review_retained_coherent_memory(store, *retained)


def test_deleted_foreign_tail_must_not_appear_as_unchanged_prefix(tmp_path):
    store, _, retained = _case(tmp_path)
    tail = _append(store, "owner-b", "two")
    _delete_row_and_event(store, tail)
    with closing(sqlite3.connect(store.path)) as connection:
        assert connection.execute(
            "SELECT seq FROM sqlite_sequence WHERE name='memory_events'"
        ).fetchone() == (2,)
    with pytest.raises(MemoryCoherentHistoryRejected, match="high-water"):
        review_retained_coherent_memory(store, *retained)


def test_deleted_only_event_cannot_recreate_empty_genesis(tmp_path):
    store = SQLiteMemoryStore(tmp_path / "empty-history.sqlite", clock_ms=lambda: 1000)
    retained = (
        capture_local_memory_event_prefix(store),
        review_memory_event_alignment(store),
    )
    only = _append(store, "owner-b", "one")
    _delete_row_and_event(store, only)
    with pytest.raises(MemoryCoherentHistoryRejected, match="high-water"):
        review_retained_coherent_memory(store, *retained)


def test_valid_other_owner_append_stays_read_only_and_unauthenticated(tmp_path):
    store, _, retained = _case(tmp_path)
    _append(store, "owner-b", "two")
    report = review_retained_coherent_memory(store, *retained)
    assert (report.previous_event_count, report.current_event_count) == (1, 2)
    assert report.status == "ADVANCED_PREFIX_UNAUTHENTICATED"
    assert report.independently_authenticated is False
    assert report.historical_writer_authenticated is False
    assert report.action_authorized is False
    assert report.memory_disclosure_authorized is False
