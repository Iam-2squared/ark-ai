"""Memory alignment never hydrates corrupt giant SQLite TEXT before denial.

Synthetic data only, one read snapshot; this is not an external provenance
or erasure proof and does not modify the frozen Memory v1 schema.
"""

from __future__ import annotations

import sqlite3

import pytest

from ark.memory import MemoryScope, MemoryWrite, SQLiteMemoryStore
from ark.memory.sqlite_event_alignment import (
    MemoryEventAlignmentRejected,
    review_memory_event_alignment,
)


@pytest.mark.parametrize(
    ("table", "column", "payload", "expected"),
    [
        ("memories", "source_id", "s" * 2049, "row hydration"),
        ("memories", "content", "c" * 4000001, "row hydration"),
        ("memory_events", "namespace", "n" * 1025, "event hydration"),
        ("memory_events", "memory_id", "mem_" + "a" * 65, "event hydration"),
    ],
)
def test_corrupt_sqlite_text_rejected_before_any_alignment_row_hydration(
    tmp_path, monkeypatch, table, column, payload, expected,
):
    store = SQLiteMemoryStore(tmp_path / "memory.sqlite", clock_ms=lambda: 2000)
    store.put(MemoryWrite(MemoryScope("owner"), "fixture", "original content"))
    with sqlite3.connect(store.path) as connection:
        connection.execute(f"UPDATE {table} SET {column}=?", (payload,))
    original = store._connect_readonly
    streamed = []

    class TracingConnection:
        def __init__(self, actual):
            self._actual = actual

        def execute(self, sql, *args):
            if "SELECT * FROM memories" in sql or (
                "FROM memory_events ORDER BY event_id" in sql
            ):
                streamed.append(sql)
            return self._actual.execute(sql, *args)

        def __getattr__(self, name):
            return getattr(self._actual, name)

    monkeypatch.setattr(
        store, "_connect_readonly", lambda: TracingConnection(original()),
    )
    with pytest.raises(MemoryEventAlignmentRejected, match=expected):
        review_memory_event_alignment(store)
    assert streamed == []
    with sqlite3.connect(store.path) as connection:
        assert connection.execute(
            f"SELECT {column} FROM {table}"
        ).fetchone() == (payload,)


def test_healthy_multi_scope_alignment_survives_hydration_preflight(tmp_path):
    store = SQLiteMemoryStore(tmp_path / "memory.sqlite", clock_ms=lambda: 2000)
    for owner in ("owner-a", "owner-b"):
        store.put(MemoryWrite(MemoryScope(owner), "fixture", "valid data"))
    first = review_memory_event_alignment(store)
    second = review_memory_event_alignment(
        SQLiteMemoryStore(store.path, clock_ms=lambda: 2000),
    )
    assert first == second
    assert first.row_count == first.event_count == first.scope_count == 2
    assert first.independently_authenticated is False
    assert first.action_authorized is False
