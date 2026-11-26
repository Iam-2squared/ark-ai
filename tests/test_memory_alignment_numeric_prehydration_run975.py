"""Memory alignment audits reject numeric storage corruption before SELECT *.

All fixtures are synthetic local SQLite rows. A hash-consistent audit is not
independent provenance, a retention decision, or permission to access data.
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
    ("column", "corrupt"),
    (
        ("created_at_ms", sqlite3.Binary(b"x" * 262144)),
        ("updated_at_ms", 100.5),
        ("expires_at_ms", sqlite3.Binary(b"x" * 262144)),
        ("revision", 1.5),
    ),
)
def test_alignment_refuses_bad_numeric_storage_before_row_hydration(
    tmp_path, monkeypatch, column, corrupt,
):
    path = tmp_path / "local-alignment.sqlite3"
    store = SQLiteMemoryStore(path, clock_ms=lambda: 100)
    row = store.put(MemoryWrite(MemoryScope("owner"), "source", "synthetic"))
    with sqlite3.connect(path) as conn:
        conn.execute(
            f"UPDATE memories SET {column}=? WHERE memory_id=?",
            (corrupt, row.memory_id),
        )
    real_connect = store._connect_readonly
    seen: list[str] = []

    class GuardConnection:
        def __init__(self, actual):
            self.actual = actual

        def execute(self, sql, *args):
            if "SELECT * FROM memories" in sql or (
                "FROM memory_events ORDER BY event_id" in sql
            ):
                seen.append(sql)
                pytest.fail("corrupt row was hydrated during global alignment")
            return self.actual.execute(sql, *args)

        def __getattr__(self, name):
            return getattr(self.actual, name)

    monkeypatch.setattr(
        store, "_connect_readonly", lambda: GuardConnection(real_connect()),
    )
    with pytest.raises(MemoryEventAlignmentRejected, match="row hydration preflight"):
        review_memory_event_alignment(store)
    assert seen == []
    with sqlite3.connect(path) as conn:
        assert conn.execute("SELECT COUNT(*) FROM memories").fetchone() == (1,)
        assert conn.execute("SELECT COUNT(*) FROM memory_events").fetchone() == (1,)


def test_alignment_healthy_nullable_expiry_and_multilingual_history(tmp_path):
    store = SQLiteMemoryStore(tmp_path / "healthy.sqlite3", clock_ms=lambda: 100)
    scope = MemoryScope("日本語", "私的")
    store.put(MemoryWrite(scope, "出典", "合成テスト", expires_at_ms=200))
    store.put(MemoryWrite(scope, "別出典", "合成テスト"))
    review = review_memory_event_alignment(store)
    assert (review.row_count, review.event_count, review.scope_count) == (2, 2, 1)
    assert review.action_authorized is False
    assert review.independently_authenticated is False
