"""Retained Memory row-delta scan rejects missing local event history.

Only disposable SQLite fixtures are modified. The local AUTOINCREMENT marker
is a secondary consistency signal, never independent provenance or consent.
"""

import sqlite3

import pytest

from ark.memory import MemoryScope, MemoryWrite, SQLiteMemoryStore
from ark.memory.sqlite_retained_row_delta_review import (
    MemoryRowDeltaRejected,
    capture_local_memory_row_delta,
    review_retained_memory_row_delta,
)


def _fixture(tmp_path):
    store = SQLiteMemoryStore(
        tmp_path / "row-delta.sqlite", clock_ms=lambda: 3000,
    )
    scope = MemoryScope("local-owner", "fixture")
    a = store.put(MemoryWrite(scope, "a", "private-a"))
    assert store.delete(a.memory_id, scope, expected_revision=1)
    b = store.put(MemoryWrite(scope, "b", "private-b"))
    retained = capture_local_memory_row_delta(store)
    assert (retained.event_count, retained.last_event_id) == (3, 3)
    return store, scope, b, retained


@pytest.mark.parametrize("scenario", (
    "remove_closed_lifecycle",
    "remove_live_tail_and_row",
    "forge_highwater",
    "remove_sequence",
))
def test_capture_and_retained_review_refuse_unexplained_event_loss(
    tmp_path, scenario,
):
    store, _, b, retained = _fixture(tmp_path)
    with sqlite3.connect(store.path) as conn:
        if scenario == "remove_closed_lifecycle":
            conn.execute(
                "DELETE FROM memory_events WHERE event_id IN (1,2)"
            )
        elif scenario == "remove_live_tail_and_row":
            conn.execute(
                "DELETE FROM memories WHERE memory_id=?", (b.memory_id,),
            )
            conn.execute("DELETE FROM memory_events WHERE event_id=3")
        elif scenario == "forge_highwater":
            conn.execute(
                "UPDATE sqlite_sequence SET seq=9 "
                "WHERE name='memory_events'"
            )
        else:
            conn.execute(
                "DELETE FROM sqlite_sequence WHERE name='memory_events'"
            )
    with pytest.raises(MemoryRowDeltaRejected):
        capture_local_memory_row_delta(store)
    with pytest.raises(MemoryRowDeltaRejected):
        review_retained_memory_row_delta(store, retained)


def test_fully_removed_terminal_history_keeps_local_tail_signal(tmp_path):
    store = SQLiteMemoryStore(
        tmp_path / "emptied.sqlite", clock_ms=lambda: 3000,
    )
    scope = MemoryScope("owner", "fixture")
    record = store.put(MemoryWrite(scope, "a", "fixture"))
    assert store.delete(record.memory_id, scope, expected_revision=1)
    with sqlite3.connect(store.path) as conn:
        conn.execute("DELETE FROM memory_events")
    with pytest.raises(
        MemoryRowDeltaRejected, match="high-water",
    ):
        capture_local_memory_row_delta(store)


def test_ordinary_append_and_valid_empty_database_remain_read_only(tmp_path):
    store = SQLiteMemoryStore(
        tmp_path / "untouched.sqlite", clock_ms=lambda: 3000,
    )
    empty = capture_local_memory_row_delta(store)
    assert (empty.event_count, empty.last_event_id) == (0, 0)
    scope = MemoryScope("owner", "fixture")
    store.put(MemoryWrite(scope, "a", "first"))
    retained = capture_local_memory_row_delta(store)
    store.put(MemoryWrite(scope, "b", "second"))
    reviewed = review_retained_memory_row_delta(store, retained)
    assert reviewed.writer_authenticated is False
    assert reviewed.disclosure_authorized is False
    assert reviewed.action_authorized is False
    fresh = capture_local_memory_row_delta(store)
    assert (fresh.event_count, fresh.last_event_id) == (2, 2)
