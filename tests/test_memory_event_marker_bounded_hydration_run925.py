"""Read-only Memory event alignment bounds duplicate SQLite high-water hydration."""

from __future__ import annotations

import sqlite3

import pytest

from ark.memory import MemoryScope, MemoryWrite, SQLiteMemoryStore
from ark.memory.contracts import MemorySchemaError
from ark.memory.sqlite_event_alignment import (
    MemoryEventAlignmentRejected,
    review_memory_event_alignment,
)


@pytest.mark.parametrize("populated", [False, True])
def test_memory_alignment_sequence_query_is_bounded(
    tmp_path, monkeypatch, populated,
):
    store = SQLiteMemoryStore(tmp_path / "memory.db", clock_ms=lambda: 2000)
    if populated:
        store.put(MemoryWrite(MemoryScope("synthetic"), "note", "fixture"))
    original = store._connect_readonly
    observed = []

    class TracingConnection:
        def __init__(self, connection):
            self._connection = connection

        def execute(self, sql, *args):
            if "FROM sqlite_sequence" in sql and "memory_events" in sql:
                observed.append(sql)
            return self._connection.execute(sql, *args)

        def __getattr__(self, name):
            return getattr(self._connection, name)

    monkeypatch.setattr(
        store, "_connect_readonly",
        lambda: TracingConnection(original()),
    )
    report = review_memory_event_alignment(store)
    assert report.event_count == int(populated)
    assert observed
    assert all("LIMIT 2" in query for query in observed)
    assert report.action_authorized is False
    assert report.independently_authenticated is False


@pytest.mark.parametrize("forged_count", [1, 2, 64])
def test_forged_high_water_rows_fail_closed_without_repair(tmp_path, forged_count):
    store = SQLiteMemoryStore(tmp_path / "memory.db", clock_ms=lambda: 2000)
    store.put(MemoryWrite(MemoryScope("synthetic"), "note", "fixture"))
    with sqlite3.connect(store.path) as connection:
        connection.executemany(
            "INSERT INTO sqlite_sequence(name, seq) VALUES ('memory_events', ?)",
            [(1,)] * forged_count,
        )
        before = connection.execute(
            "SELECT COUNT(*) FROM sqlite_sequence WHERE name='memory_events'"
        ).fetchone()[0]
        assert before == forged_count + 1
    # A lower-level schema preflight may reject the same corruption earlier;
    # neither rejection is authority to rewrite or silently truncate history.
    with pytest.raises((MemoryEventAlignmentRejected, MemorySchemaError)):
        review_memory_event_alignment(store)
    with sqlite3.connect(store.path) as connection:
        after = connection.execute(
            "SELECT COUNT(*) FROM sqlite_sequence WHERE name='memory_events'"
        ).fetchone()[0]
        assert after == before


def test_normal_memory_alignment_remains_stable_across_restart(tmp_path):
    path = tmp_path / "memory.db"
    store = SQLiteMemoryStore(path, clock_ms=lambda: 2000)
    store.put(MemoryWrite(MemoryScope("synthetic"), "note", "fixture"))
    before = review_memory_event_alignment(store)
    restarted = SQLiteMemoryStore(path, clock_ms=lambda: 2000)
    after = review_memory_event_alignment(restarted)
    assert before == after
    assert after.event_count == 1
    assert after.deletion_or_erasure_proven is False
