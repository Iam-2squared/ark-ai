"""Real SQLite ABA and competing-handle coverage for opt-in generation CAS.

Local synthetic fixtures only: neither a retained token nor a winning CAS
authenticates a writer, grants consent, or authorizes an external action.
"""

from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
from threading import Barrier

import pytest

from ark.memory import MemoryScope, MemoryWrite, SQLiteMemoryStore
from ark.memory.contracts import MemoryConflictError
from ark.memory.generation_fenced_cas import (
    generation_fenced_memory_update,
    observe_memory_generation_for_cas,
)


def _setup(tmp_path):
    path = tmp_path / "generation-contention.sqlite3"
    scope = MemoryScope("local-owner", "private")
    first = SQLiteMemoryStore(path, clock_ms=lambda: 200)
    row = first.put(MemoryWrite(scope, "shared-source", "stable"))
    token = observe_memory_generation_for_cas(first, scope, "shared-source")
    return path, scope, first, row, token


def _ops(store, scope):
    return [(event.operation, event.revision) for event in store.events(scope)]


@pytest.mark.parametrize("recreated_content", ["stable", "different"])
def test_deleted_and_recreated_generation_rejects_original_token(
    tmp_path, recreated_content,
):
    path, scope, first, row, stale = _setup(tmp_path)
    assert first.delete(row.memory_id, scope, expected_revision=1)
    fresh = SQLiteMemoryStore(path, clock_ms=lambda: 300)
    recreated = fresh.put(MemoryWrite(scope, "shared-source", recreated_content))
    assert recreated.memory_id == row.memory_id
    assert recreated.revision == row.revision == 1

    with pytest.raises(MemoryConflictError, match="generation changed"):
        generation_fenced_memory_update(
            fresh, MemoryWrite(scope, "shared-source", "stale rewrite"),
            retained=stale,
        )
    cold = SQLiteMemoryStore(path, clock_ms=lambda: 301)
    assert cold.get(row.memory_id, scope) == recreated
    assert _ops(cold, scope) == [
        ("create", 1), ("delete", 1), ("create", 1),
    ]


def test_successful_token_cannot_be_used_twice_after_reopen(tmp_path):
    path, scope, first, row, retained = _setup(tmp_path)
    changed = generation_fenced_memory_update(
        first, MemoryWrite(scope, "shared-source", "once"), retained=retained,
    )
    assert changed.revision == 2
    cold = SQLiteMemoryStore(path, clock_ms=lambda: 201)
    with pytest.raises(MemoryConflictError, match="generation changed"):
        generation_fenced_memory_update(
            cold, MemoryWrite(scope, "shared-source", "twice"),
            retained=retained,
        )
    assert cold.get(row.memory_id, scope) == changed
    assert _ops(cold, scope) == [("create", 1), ("update", 2)]


def test_generation_token_survives_reopen_without_intervening_write(tmp_path):
    path, scope, _, row, retained = _setup(tmp_path)
    cold = SQLiteMemoryStore(path, clock_ms=lambda: 201)
    changed = generation_fenced_memory_update(
        cold, MemoryWrite(scope, "shared-source", "reopened"),
        retained=retained,
    )
    assert changed.revision == 2
    assert cold.get(row.memory_id, scope) == changed
    assert _ops(cold, scope) == [("create", 1), ("update", 2)]


def test_foreign_scope_append_does_not_stale_unrelated_generation(tmp_path):
    path, scope, first, row, retained = _setup(tmp_path)
    foreign = MemoryScope("other-owner", "private")
    second = SQLiteMemoryStore(path, clock_ms=lambda: 201)
    other = second.put(MemoryWrite(foreign, "shared-source", "foreign"))
    changed = generation_fenced_memory_update(
        first, MemoryWrite(scope, "shared-source", "local-update"),
        retained=retained,
    )
    assert changed.revision == 2
    cold = SQLiteMemoryStore(path, clock_ms=lambda: 202)
    assert cold.get(row.memory_id, scope) == changed
    assert cold.get(other.memory_id, foreign) == other
    assert _ops(cold, scope) == [("create", 1), ("update", 2)]
    assert _ops(cold, foreign) == [("create", 1)]


def test_two_independent_handles_have_exactly_one_cas_winner(tmp_path):
    path, scope, _, row, retained = _setup(tmp_path)
    gate = Barrier(2)

    def attempt(value):
        local = SQLiteMemoryStore(path, clock_ms=lambda: 203)
        gate.wait(timeout=15)
        try:
            item = generation_fenced_memory_update(
                local, MemoryWrite(scope, "shared-source", value),
                retained=retained,
            )
        except MemoryConflictError:
            return ("conflict", None)
        return ("success", item)

    with ThreadPoolExecutor(max_workers=2) as executor:
        tasks = [executor.submit(attempt, label) for label in ("a", "b")]
        results = [future.result(timeout=30) for future in tasks]

    winners = [item for outcome, item in results if outcome == "success"]
    losers = [outcome for outcome, _ in results if outcome == "conflict"]
    assert len(winners) == len(losers) == 1
    cold = SQLiteMemoryStore(path, clock_ms=lambda: 204)
    assert cold.get(row.memory_id, scope) == winners[0]
    assert winners[0].revision == 2
    assert _ops(cold, scope) == [("create", 1), ("update", 2)]
