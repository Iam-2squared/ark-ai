"""Concurrent generation-fenced Memory CAS: one persisted winner, no replay.

All work is local, with temporary SQLite databases and a synthetic clock.
This tests integrity under two writer handles, never permission or consent.
"""

from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
from threading import Barrier

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
from ark.memory.sqlite_event_alignment import review_memory_event_alignment


@pytest.mark.parametrize("owner", ("alice", "bob", "日本語"))
def test_two_writers_with_same_generation_commit_exactly_once(tmp_path, owner):
    path = tmp_path / "cas competing writers #1.sqlite"
    def clock():
        return 100
    first = SQLiteMemoryStore(path, clock_ms=clock)
    second = SQLiteMemoryStore(path, clock_ms=clock)
    scope = MemoryScope(owner, "private")
    created = first.put(MemoryWrite(scope, "source", "before"))
    retained = observe_memory_generation_for_cas(first, scope, "source")
    assert retained.revision == 1
    assert retained.external_action_authorized is False
    barrier = Barrier(2)

    def attempt(args):
        store, payload = args
        barrier.wait(timeout=10)
        try:
            result = generation_fenced_memory_update(
                store, MemoryWrite(scope, "source", payload), retained=retained,
            )
        except MemoryConflictError:
            return "conflict", None
        return "committed", result

    with ThreadPoolExecutor(max_workers=2) as workers:
        outcomes = list(workers.map(attempt, (
            (first, "candidate-1"), (second, "candidate-2"),
        )))
    assert sorted(state for state, _ in outcomes) == ["committed", "conflict"]
    winning = next(record for state, record in outcomes if state == "committed")
    assert winning is not None
    assert winning.revision == 2
    assert winning.content in ("candidate-1", "candidate-2")
    assert first.get(created.memory_id, scope, include_expired=True) == winning
    assert second.get(created.memory_id, scope, include_expired=True) == winning

    evidence = review_memory_event_alignment(second)
    assert (evidence.row_count, evidence.event_count, evidence.last_event_id) == (1, 2, 2)
    assert evidence.action_authorized is False

    with pytest.raises(MemoryConflictError, match="generation changed"):
        generation_fenced_memory_update(
            first, MemoryWrite(scope, "source", "forbidden replay"), retained=retained,
        )
    assert review_memory_event_alignment(first) == evidence
