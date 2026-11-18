"""Run958: a WAL checkpoint must not change a Memory generation lifetime.

Only disposable local SQLite bytes are touched. Generation tokens never
convey consent, trusted time, or authorization for an external tool action.
"""

from __future__ import annotations

import sqlite3

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


@pytest.mark.parametrize("checkpoint", ("PASSIVE", "FULL", "TRUNCATE"))
def test_cold_wal_checkpoint_keeps_cas_event_prefix_and_stale_denial(
    tmp_path, checkpoint: str,
) -> None:
    path = tmp_path / "synthetic-wal-generation.sqlite"
    scope = MemoryScope("synthetic-owner", "private")
    initial = SQLiteMemoryStore(path, clock_ms=lambda: 100)
    created = initial.put(MemoryWrite(scope, "source", "first"))
    observed = observe_memory_generation_for_cas(initial, scope, "source")
    assert observed.external_action_authorized is False
    assert observed.consent_authenticated is False

    with sqlite3.connect(path) as conn:
        assert conn.execute("PRAGMA journal_mode=WAL").fetchone() == ("wal",)
        # This rewrites physical SQLite storage, never logical event history.
        checkpoint_result = conn.execute(
            f"PRAGMA wal_checkpoint({checkpoint})"
        ).fetchone()
        assert checkpoint_result is not None
        assert checkpoint_result[0] == 0

    cold = SQLiteMemoryStore(path, clock_ms=lambda: 110)
    updated = generation_fenced_memory_update(
        cold,
        MemoryWrite(scope, "source", "second"),
        retained=observed,
    )
    assert updated.memory_id == created.memory_id
    assert updated.revision == 2
    assert updated.content == "second"

    with pytest.raises(MemoryConflictError):
        generation_fenced_memory_update(
            SQLiteMemoryStore(path, clock_ms=lambda: 120),
            MemoryWrite(scope, "source", "must-not-append"),
            retained=observed,
        )

    again = SQLiteMemoryStore(path, clock_ms=lambda: 130)
    final = again.get(created.memory_id, scope)
    assert final is not None
    assert final.content == "second"
    assert final.revision == 2
    with sqlite3.connect(path) as conn:
        assert conn.execute("PRAGMA quick_check").fetchone() == ("ok",)
        assert conn.execute(
            "SELECT operation,revision FROM memory_events ORDER BY event_id"
        ).fetchall() == [("create", 1), ("update", 2)]
