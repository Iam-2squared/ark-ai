"""Two-writer Memory COMMIT uncertainty stays diagnostic after restart.

Disposable SQLite and synthetic clocks only. A matching row is not a proof
that the caller committed it, nor consent, nor permission to retry.
"""

from __future__ import annotations

import sqlite3
from concurrent.futures import ThreadPoolExecutor
from threading import Barrier

import pytest

from ark.memory import MemoryConflictError, MemoryScope, MemoryWrite, SQLiteMemoryStore
from ark.memory.ambiguous_commit_pair_review import (
    review_memory_ambiguous_commit_pair,
)
from ark.memory.generation_fenced_cas import (
    generation_fenced_memory_update,
    observe_memory_generation_for_cas,
)


@pytest.mark.parametrize("owner", ("private-owner", "日本語"))
def test_competing_cas_has_one_winner_but_no_attributed_commit(tmp_path, owner):
    path = tmp_path / "uncertain-two-handles.sqlite"
    first = SQLiteMemoryStore(path, clock_ms=lambda: 1000)
    second = SQLiteMemoryStore(path, clock_ms=lambda: 1100)
    scope = MemoryScope(owner, "private")
    saved = first.put(MemoryWrite(scope, "stable", "initial"))
    retained = observe_memory_generation_for_cas(first, scope, "stable")
    barrier = Barrier(2)

    def attempt(args):
        store, candidate = args
        barrier.wait(timeout=10)
        try:
            generation_fenced_memory_update(
                store, MemoryWrite(scope, "stable", candidate),
                retained=retained,
            )
        except MemoryConflictError:
            return ("conflict", candidate)
        return ("committed", candidate)

    with ThreadPoolExecutor(max_workers=2) as workers:
        outcomes = list(workers.map(
            attempt, ((first, "candidate-a"), (second, "candidate-b")),
        ))
    assert sorted(state for state, _ in outcomes) == ["committed", "conflict"]
    winner = next(value for state, value in outcomes if state == "committed")

    reopened = SQLiteMemoryStore(path, clock_ms=lambda: 1200)
    record = reopened.get(saved.memory_id, scope, include_expired=True)
    assert (record.revision, record.content) == (2, winner)
    with sqlite3.connect(path) as conn:
        before = tuple(conn.iterdump())
    report = review_memory_ambiguous_commit_pair(
        reopened, MemoryWrite(scope, "stable", winner), retained=retained,
    )
    assert report.disposition == "MATCHING_ROW_MANUAL_REVIEW"
    assert report.caller_commit_authenticated is False
    assert report.automatic_retry_authorized is False
    assert report.write_authorized is False
    assert report.trusted_clock_verified is False
    with sqlite3.connect(path) as conn:
        assert tuple(conn.iterdump()) == before

    with pytest.raises(MemoryConflictError):
        generation_fenced_memory_update(
            reopened, MemoryWrite(scope, "stable", "must-not-replay"),
            retained=retained,
        )
    assert reopened.get(saved.memory_id, scope, include_expired=True) == record


def test_unrelated_writer_replacement_is_divergence_not_permission(tmp_path):
    path = tmp_path / "replaced-by-other-handle.sqlite"
    writer = SQLiteMemoryStore(path, clock_ms=lambda: 1000)
    observer = SQLiteMemoryStore(path, clock_ms=lambda: 1200)
    scope = MemoryScope("owner", "private")
    writer.put(MemoryWrite(scope, "stable", "original"))
    retained = observe_memory_generation_for_cas(observer, scope, "stable")
    generation_fenced_memory_update(
        writer, MemoryWrite(scope, "stable", "different"),
        retained=retained,
    )
    result = review_memory_ambiguous_commit_pair(
        observer, MemoryWrite(scope, "stable", "proposed"), retained=retained,
    )
    assert result.disposition == "DIVERGED_MANUAL_REVIEW"
    assert result.automatic_retry_authorized is False
    assert result.caller_commit_authenticated is False


def test_second_interleaved_generation_is_not_one_matching_update(tmp_path):
    path = tmp_path / "two-updates.sqlite"
    writer = SQLiteMemoryStore(path, clock_ms=lambda: 1000)
    observer = SQLiteMemoryStore(path, clock_ms=lambda: 1200)
    scope = MemoryScope("owner", "private")
    writer.put(MemoryWrite(scope, "stable", "original"))
    retained = observe_memory_generation_for_cas(observer, scope, "stable")
    proposed = MemoryWrite(scope, "stable", "proposed")
    generation_fenced_memory_update(writer, proposed, retained=retained)
    next_token = observe_memory_generation_for_cas(writer, scope, "stable")
    generation_fenced_memory_update(writer, proposed, retained=next_token)
    report = review_memory_ambiguous_commit_pair(
        observer, proposed, retained=retained,
    )
    assert report.disposition == "DIVERGED_MANUAL_REVIEW"
    assert report.caller_commit_authenticated is False
    assert report.automatic_retry_authorized is False
