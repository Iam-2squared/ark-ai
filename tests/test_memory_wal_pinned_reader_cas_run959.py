"""Run959: WAL readers cannot confer authority or erase CAS history.

Pinned historical SQLite read snapshots may be stale, but a separate writer
must commit a new generation and reject any replay of the old CAS token.
Only disposable local files and synthetic Memory data are used.
"""

from __future__ import annotations

import sqlite3
from contextlib import ExitStack, closing

import pytest

from ark.memory import (
    MemoryConflictError,
    MemoryScope,
    MemoryWrite,
    SQLiteMemoryStore,
)
from ark.memory.generation_fenced_cas import (
    generation_fenced_memory_update,
    observe_memory_generation_for_cas,
)


@pytest.mark.parametrize("pinned_readers", (1, 2))
def test_wal_pinned_readers_remain_historical_while_writer_cas_advances(
    tmp_path, pinned_readers: int,
) -> None:
    path = tmp_path / "isolated-wal-cas.sqlite"
    scope = MemoryScope("fixture-owner", "private")
    initial = SQLiteMemoryStore(path, clock_ms=lambda: 100)
    created = initial.put(MemoryWrite(scope, "source", "before"))
    retained = observe_memory_generation_for_cas(initial, scope, "source")
    assert retained.external_action_authorized is False
    assert retained.consent_authenticated is False

    with sqlite3.connect(path) as conn:
        assert conn.execute("PRAGMA journal_mode=WAL").fetchone() == ("wal",)

    with ExitStack() as stack:
        readers = [
            stack.enter_context(closing(sqlite3.connect(
                path, isolation_level=None, timeout=3,
            )))
            for _ in range(pinned_readers)
        ]
        for reader in readers:
            reader.execute("PRAGMA query_only=ON")
            reader.execute("BEGIN")
            assert reader.execute(
                "SELECT revision,content FROM memories WHERE memory_id=?",
                (created.memory_id,),
            ).fetchone() == (1, "before")
            assert reader.execute(
                "SELECT operation,revision FROM memory_events ORDER BY event_id"
            ).fetchall() == [("create", 1)]

        # A pinned reader must not block an independent WAL writer, and its
        # historical view is never a write token or trusted authorization.
        updated = generation_fenced_memory_update(
            SQLiteMemoryStore(path, clock_ms=lambda: 110),
            MemoryWrite(scope, "source", "after"),
            retained=retained,
        )
        assert updated.revision == 2
        assert updated.content == "after"
        for reader in readers:
            assert reader.execute(
                "SELECT revision,content FROM memories WHERE memory_id=?",
                (created.memory_id,),
            ).fetchone() == (1, "before")

        with sqlite3.connect(path) as checkpointer:
            result = checkpointer.execute(
                "PRAGMA wal_checkpoint(PASSIVE)"
            ).fetchone()
            assert result is not None
            assert result[0] == 0

        with pytest.raises(MemoryConflictError):
            generation_fenced_memory_update(
                SQLiteMemoryStore(path, clock_ms=lambda: 120),
                MemoryWrite(scope, "source", "must-not-replay"),
                retained=retained,
            )
        for reader in readers:
            reader.execute("ROLLBACK")
            assert reader.execute(
                "SELECT revision,content FROM memories WHERE memory_id=?",
                (created.memory_id,),
            ).fetchone() == (2, "after")

    cold = SQLiteMemoryStore(path, clock_ms=lambda: 130)
    current = cold.get(created.memory_id, scope)
    assert current is not None
    assert current.content == "after"
    assert current.revision == 2
    with sqlite3.connect(path) as conn:
        assert conn.execute(
            "SELECT operation,revision FROM memory_events ORDER BY event_id"
        ).fetchall() == [("create", 1), ("update", 2)]
        assert conn.execute("PRAGMA quick_check").fetchone() == ("ok",)
