"""A lost response after local Memory deletion or expiry cannot restore a row.

These are disposable SQLite fixtures. A committed DELETE/expire event is
local evidence only, not physical erasure of backups, consent, permission to
delete real user data, or a distributed exactly-once guarantee.
"""

from __future__ import annotations

import os
from multiprocessing import get_context

import pytest

from ark.memory import MemoryConflictError, MemoryScope, MemoryWrite, SQLiteMemoryStore
from ark.memory.generation_fenced_cas import (
    MemoryGenerationCASRejected,
    generation_fenced_memory_update,
    observe_memory_generation_for_cas,
)


def _delete_then_exit(path: str, memory_id: str, mode: str) -> None:
    scope = MemoryScope("expiry-process-fixture", "private")
    store = SQLiteMemoryStore(path, clock_ms=lambda: 205)
    if mode == "delete":
        assert store.delete(memory_id, scope, expected_revision=1) is True
    else:
        assert store.purge_expired(scope=scope, limit=1) == 1
    os._exit(0)  # SQLite committed; the caller receives no acknowledgement.


@pytest.mark.parametrize(("mode", "operation"), (("delete", "delete"), ("purge", "expire")))
def test_cold_memory_delete_and_purge_commit_unknown_never_replay(
    tmp_path, mode, operation,
):
    path = tmp_path / "memory-delete-lost-response.sqlite3"
    private = MemoryScope("expiry-process-fixture", "private")
    other = MemoryScope("expiry-process-fixture", "notes")
    writer = SQLiteMemoryStore(path, clock_ms=lambda: 200)
    target = writer.put(
        MemoryWrite(private, "expiring", "private-to-delete", expires_at_ms=201),
    )
    safe = writer.put(
        MemoryWrite(other, "keep", "independent", expires_at_ms=500),
    )
    old_token = observe_memory_generation_for_cas(writer, private, "expiring")

    child = get_context("spawn").Process(
        target=_delete_then_exit, args=(str(path), target.memory_id, mode),
    )
    child.start()
    child.join(timeout=35)
    if child.is_alive():
        child.terminate()
        child.join(timeout=5)
    assert child.exitcode == 0, "worker did not reach the committed deletion"

    cold = SQLiteMemoryStore(path, clock_ms=lambda: 205)
    assert cold.get(target.memory_id, private, include_expired=True) is None
    other_row = cold.get(safe.memory_id, other, include_expired=True)
    assert other_row is not None and other_row.content == "independent"
    original_events = tuple(cold.events(private))
    assert [(event.operation, event.revision) for event in original_events] == [
        ("create", 1), (operation, 1),
    ]

    with pytest.raises((MemoryConflictError, MemoryGenerationCASRejected)):
        generation_fenced_memory_update(
            cold, MemoryWrite(private, "expiring", "never-resurrect"),
            retained=old_token,
        )
    assert cold.get(target.memory_id, private, include_expired=True) is None
    assert tuple(cold.events(private)) == original_events
    assert cold.get(safe.memory_id, other, include_expired=True) == other_row
