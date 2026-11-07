"""Read-only Memory event prefix rejects local AUTOINCREMENT tail loss.

All corruption is confined to disposable SQLite fixtures. This local
consistency marker is not a writer identity, retained custody, or consent.
"""

import sqlite3

import pytest

from ark.memory import MemoryScope, MemoryWrite, SQLiteMemoryStore
from ark.memory.sqlite_event_prefix_review import (
    MemoryEventPrefixRejected,
    capture_local_memory_event_prefix,
    compare_local_memory_event_prefix,
)


def _fixture(tmp_path):
    store = SQLiteMemoryStore(
        tmp_path / "event-prefix.sqlite", clock_ms=lambda: 7000,
    )
    scope = MemoryScope("local-owner", "offline-fixture")
    store.put(MemoryWrite(scope, "first", "private first"))
    retained = capture_local_memory_event_prefix(store)
    store.put(MemoryWrite(scope, "second", "private second"))
    return store, retained


@pytest.mark.parametrize("scenario", (
    "truncate_last",
    "truncate_all",
    "advance_sequence",
    "remove_sequence",
))
def test_event_prefix_refuses_invalid_append_highwater(tmp_path, scenario):
    store, retained = _fixture(tmp_path)
    with sqlite3.connect(store.path) as conn:
        if scenario == "truncate_last":
            conn.execute("DELETE FROM memory_events WHERE event_id=2")
        elif scenario == "truncate_all":
            conn.execute("DELETE FROM memory_events")
        elif scenario == "advance_sequence":
            conn.execute(
                "UPDATE sqlite_sequence SET seq=99 WHERE name='memory_events'"
            )
        else:
            conn.execute(
                "DELETE FROM sqlite_sequence WHERE name='memory_events'"
            )
    with pytest.raises(MemoryEventPrefixRejected):
        capture_local_memory_event_prefix(store)
    with pytest.raises(MemoryEventPrefixRejected):
        compare_local_memory_event_prefix(store, retained)


def test_empty_removed_terminal_history_cannot_look_like_genesis(tmp_path):
    store = SQLiteMemoryStore(
        tmp_path / "terminal.sqlite", clock_ms=lambda: 7000,
    )
    scope = MemoryScope("local-owner", "offline-fixture")
    row = store.put(MemoryWrite(scope, "first", "private"))
    assert store.delete(row.memory_id, scope, expected_revision=1)
    with sqlite3.connect(store.path) as conn:
        conn.execute("DELETE FROM memory_events")
    with pytest.raises(MemoryEventPrefixRejected, match="high-water"):
        capture_local_memory_event_prefix(store)


def test_ordinary_genesis_append_and_readonly_review_preserved(tmp_path):
    store = SQLiteMemoryStore(
        tmp_path / "ordinary.sqlite", clock_ms=lambda: 7000,
    )
    empty = capture_local_memory_event_prefix(store)
    assert empty.event_count == 0
    scope = MemoryScope("local-owner", "offline-fixture")
    store.put(MemoryWrite(scope, "first", "private first"))
    retained = capture_local_memory_event_prefix(store)
    store.put(MemoryWrite(scope, "second", "private second"))
    with sqlite3.connect(store.path) as conn:
        before = tuple(conn.iterdump())
    result = compare_local_memory_event_prefix(store, retained)
    assert result.current_event_count == 2
    assert result.historical_writer_authenticated is False
    assert result.action_authorized is False
    with sqlite3.connect(store.path) as conn:
        assert tuple(conn.iterdump()) == before
