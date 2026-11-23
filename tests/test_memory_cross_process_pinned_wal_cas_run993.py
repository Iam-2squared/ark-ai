"""Run993: cross-process WAL readers preserve snapshot isolation during CAS writers."""

from __future__ import annotations

import sqlite3
from multiprocessing import get_context
from pathlib import Path

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


def _pinned_reader(path, ready, release, results) -> None:
    connection = sqlite3.connect(path, timeout=20, isolation_level=None)
    try:
        connection.execute("PRAGMA query_only=ON")
        connection.execute("BEGIN")
        before_row = connection.execute(
            "SELECT memory_id,revision,content FROM memories ORDER BY memory_id"
        ).fetchone()
        before_events = tuple(connection.execute(
            "SELECT event_id,operation,revision FROM memory_events ORDER BY event_id"
        ).fetchall())
        ready.set()
        if not release.wait(30):
            results.put(("reader-timeout",))
            return

        pinned_row = connection.execute(
            "SELECT memory_id,revision,content FROM memories ORDER BY memory_id"
        ).fetchone()
        pinned_events = tuple(connection.execute(
            "SELECT event_id,operation,revision FROM memory_events ORDER BY event_id"
        ).fetchall())
        connection.execute("ROLLBACK")

        connection.execute("BEGIN")
        after_row = connection.execute(
            "SELECT memory_id,revision,content FROM memories ORDER BY memory_id"
        ).fetchone()
        after_events = tuple(connection.execute(
            "SELECT event_id,operation,revision FROM memory_events ORDER BY event_id"
        ).fetchall())
        connection.execute("ROLLBACK")
        results.put((
            "reader", before_row, before_events, pinned_row,
            pinned_events, after_row, after_events,
        ))
    finally:
        connection.close()


def _competing_writer(path, retained, barrier, results, candidate, at_ms) -> None:
    try:
        barrier.wait(timeout=20)
        scope = MemoryScope("fixture-owner", "private")
        store = SQLiteMemoryStore(Path(path), clock_ms=lambda: at_ms)
        updated = generation_fenced_memory_update(
            store,
            MemoryWrite(scope, "source", candidate),
            retained=retained,
        )
        results.put(("writer", "updated", candidate, updated.revision))
    except MemoryConflictError:
        results.put(("writer", "conflict", candidate))
    except Exception as exc:
        results.put(("writer", "error", candidate, type(exc).__name__))


def test_cross_process_pinned_wal_reader_and_competing_cas_writers(tmp_path: Path):
    path = tmp_path / "cross-process-pinned-wal.sqlite"
    scope = MemoryScope("fixture-owner", "private")
    initial = SQLiteMemoryStore(path, clock_ms=lambda: 100)
    created = initial.put(MemoryWrite(scope, "source", "before"))
    retained = observe_memory_generation_for_cas(initial, scope, "source")
    assert retained.external_action_authorized is False
    assert retained.consent_authenticated is False

    with sqlite3.connect(path) as connection:
        assert connection.execute("PRAGMA journal_mode=WAL").fetchone() == ("wal",)

    context = get_context("spawn")
    reader_ready = context.Event()
    reader_release = context.Event()
    results = context.Queue()
    reader = context.Process(
        target=_pinned_reader,
        args=(str(path), reader_ready, reader_release, results),
    )
    writers = []
    started = []
    try:
        reader.start()
        started.append(reader)
        assert reader_ready.wait(20), "independent WAL reader did not pin its snapshot"

        barrier = context.Barrier(2)
        writers = [
            context.Process(
                target=_competing_writer,
                args=(str(path), retained, barrier, results, "candidate-a", 110),
            ),
            context.Process(
                target=_competing_writer,
                args=(str(path), retained, barrier, results, "candidate-b", 111),
            ),
        ]
        for process in writers:
            process.start()
            started.append(process)
        for process in writers:
            process.join(timeout=35)
            if process.is_alive():
                process.terminate()
                process.join(timeout=5)
            assert process.exitcode == 0

        outcomes = [results.get(timeout=10), results.get(timeout=10)]
        assert all(item[0] == "writer" for item in outcomes)
        assert sorted(item[1] for item in outcomes) == ["conflict", "updated"]
        winner = next(item[2] for item in outcomes if item[1] == "updated")
        assert next(item[3] for item in outcomes if item[1] == "updated") == 2

        cold = SQLiteMemoryStore(path, clock_ms=lambda: 120)
        current = cold.get(created.memory_id, scope, include_expired=True)
        assert current is not None
        assert (current.revision, current.content) == (2, winner)
        assert [
            (event.event_id, event.operation, event.revision)
            for event in cold.events(scope)
        ] == [(1, "create", 1), (2, "update", 2)]

        # The losing process and a later process cannot replay the retained
        # pre-write generation, even while the original reader is still pinned.
        with pytest.raises(MemoryConflictError):
            generation_fenced_memory_update(
                cold,
                MemoryWrite(scope, "source", "must-not-replay"),
                retained=retained,
            )

        reader_release.set()
        reader.join(timeout=20)
        assert reader.exitcode == 0
        reader_result = results.get(timeout=10)
        assert reader_result[0] == "reader"
        before_row, before_events = reader_result[1], reader_result[2]
        pinned_row, pinned_events = reader_result[3], reader_result[4]
        after_row, after_events = reader_result[5], reader_result[6]
        assert before_row == pinned_row == (created.memory_id, 1, "before")
        assert before_events == pinned_events == ((1, "create", 1),)
        assert after_row == (created.memory_id, 2, winner)
        assert after_events == ((1, "create", 1), (2, "update", 2))

        with sqlite3.connect(path) as connection:
            assert connection.execute("PRAGMA quick_check").fetchone() == ("ok",)
    finally:
        reader_release.set()
        for process in started:
            if process.is_alive():
                process.terminate()
            process.join(timeout=5)
        results.close()
        results.join_thread()
