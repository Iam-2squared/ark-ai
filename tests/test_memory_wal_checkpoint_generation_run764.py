"""Disposable Memory WAL checkpoint/restart evidence for CAS and isolation.

A physical SQLite checkpoint does not provide authenticated provenance,
external exact-once effects, permission to disclose, or a fresh CAS lifetime.
"""

from __future__ import annotations

import sqlite3
from pathlib import Path

import pytest

from ark.memory import (
    MemoryConflictError,
    MemoryScope,
    MemoryWrite,
    SQLiteMemoryStore,
)
from ark.memory.cas_generation_review import review_memory_revision_reuse
from ark.memory.generation_fenced_cas import (
    MemoryGenerationCASRejected,
    generation_fenced_memory_update,
    observe_memory_generation_for_cas,
)


def _checkpoint(path: Path) -> None:
    # Only isolated temporary test databases, never the user's real Memory.
    with sqlite3.connect(path) as conn:
        busy, _log_frames, _checkpointed = conn.execute(
            "PRAGMA wal_checkpoint(TRUNCATE)"
        ).fetchone()
        assert busy == 0


@pytest.mark.parametrize("writer_restart", [False, True])
def test_wal_checkpoint_cannot_reenable_old_generation_token(
    tmp_path: Path, writer_restart: bool,
) -> None:
    path = tmp_path / "restart-aba.sqlite"
    scope = MemoryScope("synthetic-checkpoint-owner", "private")
    first = SQLiteMemoryStore(path, clock_ms=lambda: 1000)
    original = first.put(MemoryWrite(scope, "source", "old private lifetime"))
    token = observe_memory_generation_for_cas(first, scope, "source")
    _checkpoint(path)
    writer = (
        SQLiteMemoryStore(path, clock_ms=lambda: 2000)
        if writer_restart else first
    )
    assert writer.delete(original.memory_id, scope, expected_revision=1)
    renewed = writer.put(MemoryWrite(scope, "source", "new private lifetime"))
    assert renewed.revision == original.revision == 1
    assert renewed.memory_id == original.memory_id
    _checkpoint(path)

    cold = SQLiteMemoryStore(path, clock_ms=lambda: 3000)
    events_before = tuple(cold.events(scope))
    row_before = cold.get(original.memory_id, scope)
    assert row_before == renewed
    assert tuple(event.operation for event in events_before) == (
        "create", "delete", "create",
    )
    assert tuple(event.event_id for event in events_before) == (1, 2, 3)
    assert review_memory_revision_reuse(
        cold, scope, "source", expected_revision=1,
    ).revision_reuse_possible is True

    with pytest.raises((MemoryConflictError, MemoryGenerationCASRejected)):
        generation_fenced_memory_update(
            cold, MemoryWrite(scope, "source", "forbidden stale overwrite"),
            retained=token,
        )
    assert cold.get(original.memory_id, scope) == row_before
    assert tuple(cold.events(scope)) == events_before


@pytest.mark.parametrize("reopen_count", [1, 3])
def test_checkpoint_retains_global_events_without_cross_owner_leakage(
    tmp_path: Path, reopen_count: int,
) -> None:
    path = tmp_path / "scope-isolation.sqlite"
    owner_a = MemoryScope("synthetic-owner-a", "private")
    owner_b = MemoryScope("synthetic-owner-b", "private")
    first = SQLiteMemoryStore(path, clock_ms=lambda: 1000)
    row_a = first.put(MemoryWrite(owner_a, "shared-source", "secret-a"))
    row_b = first.put(MemoryWrite(owner_b, "shared-source", "secret-b"))
    assert row_a.memory_id != row_b.memory_id

    for _ in range(reopen_count):
        _checkpoint(path)
        cold = SQLiteMemoryStore(path, clock_ms=lambda: 1000)
        assert cold.get(row_a.memory_id, owner_a) == row_a
        assert cold.get(row_b.memory_id, owner_b) == row_b
        assert cold.get(row_b.memory_id, owner_a) is None
        assert cold.get(row_a.memory_id, owner_b) is None
        assert [event.event_id for event in cold.events(owner_a)] == [1]
        assert [event.event_id for event in cold.events(owner_b)] == [2]
        assert [event.operation for event in cold.events(owner_a)] == [
            "create"
        ]
        assert [event.operation for event in cold.events(owner_b)] == [
            "create"
        ]

    assert first.get(row_a.memory_id, owner_a).content == "secret-a"
    assert first.get(row_b.memory_id, owner_b).content == "secret-b"
