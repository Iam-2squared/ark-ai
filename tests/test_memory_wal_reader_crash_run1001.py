"""Run1001: a crashed pinned WAL reader releases the final local lock.

The reader is terminated without ROLLBACK or close after an independent writer
commits a row/event pair. Reopening must recover the committed generation,
release the stale reader lock, and preserve stale-CAS rejection. Synthetic
local SQLite only; this is not power-loss, fsync, or external-effect proof.
"""

from __future__ import annotations

import os
import sqlite3
import time
from contextlib import closing
from multiprocessing import get_context
from pathlib import Path

import pytest

from ark.memory import MemoryConflictError, MemoryScope, MemoryWrite, SQLiteMemoryStore
from ark.memory.generation_fenced_cas import (
    generation_fenced_memory_update,
    observe_memory_generation_for_cas,
)


def _crash_pinned_reader_after_writer_commit(
    database: str, ready: str, writer_done: str, reader_mode: str,
) -> None:
    path = Path(database)
    target = path.as_uri() + "?mode=ro" if reader_mode == "ro" else str(path)
    connection = sqlite3.connect(
        target,
        uri=reader_mode == "ro",
        timeout=10,
        isolation_level=None,
    )
    connection.execute("BEGIN")

    def snapshot() -> tuple[int, int]:
        row = connection.execute(
            "SELECT revision FROM memories "
            "WHERE owner_id=? AND namespace=? AND source_id=?",
            ("run1001-reader-owner", "private", "source"),
        ).fetchone()
        events = connection.execute(
            "SELECT COUNT(*) FROM memory_events",
        ).fetchone()[0]
        return row[0], events

    assert snapshot() == (1, 1)
    Path(ready).touch()
    deadline = time.monotonic() + 25
    while not Path(writer_done).exists():
        if time.monotonic() >= deadline:
            os._exit(2)
        time.sleep(0.02)

    # The read transaction must retain its old snapshot even after the
    # independent writer commits. Exit without rollback or connection close.
    assert snapshot() == (1, 1)
    os._exit(0)


def _await_marker(path: Path, process) -> None:
    deadline = time.monotonic() + 25
    while not path.exists():
        if process.exitcode is not None:
            raise AssertionError("pinned WAL reader exited before its barrier")
        if time.monotonic() >= deadline:
            raise AssertionError("pinned WAL reader barrier timed out")
        time.sleep(0.02)


@pytest.mark.parametrize("reader_mode", ("ro", "rw"))
def test_crashed_pinned_wal_reader_releases_last_lock_after_committed_write(
    tmp_path, reader_mode: str,
) -> None:
    database = tmp_path / "reader-crash-memory.sqlite3"
    scope = MemoryScope("run1001-reader-owner", "private")
    initial = SQLiteMemoryStore(database, clock_ms=lambda: 100)
    created = initial.put(MemoryWrite(scope, "source", "before"))
    retained = observe_memory_generation_for_cas(initial, scope, "source")
    ready = tmp_path / "reader-ready"
    writer_done = tmp_path / "writer-done"
    process = get_context("spawn").Process(
        target=_crash_pinned_reader_after_writer_commit,
        args=(str(database), str(ready), str(writer_done), reader_mode),
    )
    process.start()
    try:
        _await_marker(ready, process)
        changed = generation_fenced_memory_update(
            SQLiteMemoryStore(database, clock_ms=lambda: 200),
            MemoryWrite(scope, "source", "after"),
            retained=retained,
        )
        assert changed.revision == 2
        writer_done.touch()
        process.join(timeout=30)
        if process.is_alive():
            process.terminate()
            process.join(timeout=5)
        assert process.exitcode == 0

        # The process died with a pinned transaction still open. A fresh
        # managed reader must recover the committed row/event pair, and a
        # TRUNCATE checkpoint must no longer report a busy reader lock.
        cold = SQLiteMemoryStore(database, clock_ms=lambda: 300)
        assert cold.get(created.memory_id, scope) == changed
        assert [
            (event.event_id, event.operation, event.revision)
            for event in cold.events(scope)
        ] == [(1, "create", 1), (2, "update", 2)]
        with closing(sqlite3.connect(database, timeout=10)) as connection:
            checkpoint = connection.execute(
                "PRAGMA wal_checkpoint(TRUNCATE)",
            ).fetchone()
            assert checkpoint is not None
            assert checkpoint[0] == 0
            assert checkpoint[1] == checkpoint[2]
            assert connection.execute("PRAGMA quick_check").fetchone() == ("ok",)

        with pytest.raises(MemoryConflictError):
            generation_fenced_memory_update(
                SQLiteMemoryStore(database, clock_ms=lambda: 400),
                MemoryWrite(scope, "source", "must-not-replay"),
                retained=retained,
            )
        reopened = SQLiteMemoryStore(database, clock_ms=lambda: 500)
        assert reopened.get(created.memory_id, scope) == changed
        assert [
            (event.event_id, event.operation, event.revision)
            for event in reopened.events(scope)
        ] == [(1, "create", 1), (2, "update", 2)]
    finally:
        if process.is_alive():
            process.terminate()
            process.join(timeout=5)
