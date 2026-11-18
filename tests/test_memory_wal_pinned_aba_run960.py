"""Run960: a pinned WAL snapshot cannot revive a deleted Memory lifetime.

Disposable local SQLite only; generation CAS is neither consent nor action
authorization.  The old reader is intentionally historical while new rows
and event IDs advance on separate writer handles.
"""

from __future__ import annotations

import sqlite3
from contextlib import closing

import pytest

from ark.memory import MemoryConflictError, MemoryScope, MemoryWrite, SQLiteMemoryStore
from ark.memory.generation_fenced_cas import (
    generation_fenced_memory_update,
    observe_memory_generation_for_cas,
)


@pytest.mark.parametrize("replacement", ("identical", "different"))
@pytest.mark.parametrize("query_only", (False, True))
def test_pinned_wal_reader_never_resurrects_deleted_generation(
    tmp_path, replacement: str, query_only: bool,
) -> None:
    path = tmp_path / "wal-aba.sqlite3"
    scope = MemoryScope("owner", "private")
    row = SQLiteMemoryStore(path, clock_ms=lambda: 100).put(
        MemoryWrite(scope, "source", "identical"),
    )
    original = observe_memory_generation_for_cas(
        SQLiteMemoryStore(path, clock_ms=lambda: 101), scope, "source",
    )
    assert original.create_event_id == 1
    assert original.revision == 1

    with closing(sqlite3.connect(path, isolation_level=None, timeout=5)) as reader:
        if query_only:
            reader.execute("PRAGMA query_only=ON")
        reader.execute("BEGIN")
        assert reader.execute(
            "SELECT content,revision FROM memories WHERE memory_id=?",
            (row.memory_id,),
        ).fetchone() == ("identical", 1)
        assert reader.execute(
            "SELECT event_id,operation FROM memory_events ORDER BY event_id"
        ).fetchall() == [(1, "create")]

        assert SQLiteMemoryStore(path, clock_ms=lambda: 110).delete(
            row.memory_id, scope, expected_revision=1,
        )
        recreated = SQLiteMemoryStore(path, clock_ms=lambda: 120).put(
            MemoryWrite(scope, "source", replacement),
        )
        assert recreated.memory_id == row.memory_id
        assert recreated.revision == 1
        assert reader.execute(
            "SELECT content,revision FROM memories WHERE memory_id=?",
            (row.memory_id,),
        ).fetchone() == ("identical", 1)
        assert reader.execute(
            "SELECT event_id,operation FROM memory_events ORDER BY event_id"
        ).fetchall() == [(1, "create")]

        cold = SQLiteMemoryStore(path, clock_ms=lambda: 130)
        with pytest.raises(MemoryConflictError):
            generation_fenced_memory_update(
                cold, MemoryWrite(scope, "source", "must-not-replay"),
                retained=original,
            )
        latest = observe_memory_generation_for_cas(cold, scope, "source")
        assert latest.create_event_id == 3
        assert latest.create_event_id != original.create_event_id
        assert latest.external_action_authorized is False
        assert latest.consent_authenticated is False
        reader.execute("ROLLBACK")
        assert reader.execute(
            "SELECT content,revision FROM memories WHERE memory_id=?",
            (row.memory_id,),
        ).fetchone() == (replacement, 1)

    cold = SQLiteMemoryStore(path, clock_ms=lambda: 140)
    assert cold.get(row.memory_id, scope).content == replacement
    with closing(sqlite3.connect(path)) as conn:
        assert conn.execute(
            "SELECT event_id,operation,revision FROM memory_events ORDER BY event_id"
        ).fetchall() == [
            (1, "create", 1), (2, "delete", 1), (3, "create", 1),
        ]
        assert conn.execute("PRAGMA quick_check").fetchone() == ("ok",)
