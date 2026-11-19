"""Run1003: a crashed WAL reader cannot hide a surviving reader's lock.

One spawned reader exits without closing its pinned transaction after a
committed Memory row/event update. A second independent reader remains open:
TRUNCATE must remain incomplete until that final reader closes. Synthetic
local SQLite only; this is not power-loss, fsync, custody, or action proof.
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


def _snapshot(connection: sqlite3.Connection) -> tuple[object, object]:
    row = connection.execute(
        "SELECT revision,content FROM memories "
        "WHERE owner_id=? AND namespace=? AND source_id=?",
        ("run1003-reader-owner", "private", "source"),
    ).fetchone()
    events = connection.execute(
        "SELECT operation,revision FROM memory_events ORDER BY event_id"
    ).fetchall()
    return row, events


def _crash_reader_while_second_reader_survives(
    database: str, ready: str, writer_done: str, reader_mode: str,
) -> None:
    path = Path(database)
    target = path.as_uri() + "?mode=ro" if reader_mode == "ro" else str(path)
    connection = sqlite3.connect(
        target, uri=reader_mode == "ro", timeout=10, isolation_level=None,
    )
    connection.execute("BEGIN")
    assert _snapshot(connection) == ((1, "before"), [("create", 1)])
    Path(ready).touch()
    deadline = time.monotonic() + 25
    while not Path(writer_done).exists():
        if time.monotonic() >= deadline:
            os._exit(2)
        time.sleep(0.02)

    # The writer has committed revision 2, but this reader still owns its
    # revision-1 WAL snapshot. Exit without ROLLBACK or sqlite3.Connection.close.
    assert _snapshot(connection) == ((1, "before"), [("create", 1)])
    os._exit(0)


def _await_marker(path: Path, process) -> None:
    deadline = time.monotonic() + 25
    while not path.exists():
        if process.exitcode is not None:
            raise AssertionError("crashed-reader fixture exited before its barrier")
        if time.monotonic() >= deadline:
            raise AssertionError("crashed-reader fixture barrier timed out")
        time.sleep(0.02)


@pytest.mark.parametrize("reader_mode", ("ro", "rw"))
def test_crashed_wal_reader_does_not_release_surviving_reader_lock(
    tmp_path, reader_mode: str,
) -> None:
    database = tmp_path / "surviving-reader-memory.sqlite3"
    scope = MemoryScope("run1003-reader-owner", "private")
    initial = SQLiteMemoryStore(database, clock_ms=lambda: 100)
    created = initial.put(MemoryWrite(scope, "source", "before"))
    retained = observe_memory_generation_for_cas(initial, scope, "source")

    # This independent parent connection is deliberately kept open after the
    # child dies. Its read transaction must continue to see the old snapshot.
    keeper = sqlite3.connect(database, timeout=10, isolation_level=None)
    keeper.execute("PRAGMA query_only=ON")
    keeper.execute("BEGIN")
    assert _snapshot(keeper) == ((1, "before"), [("create", 1)])

    ready = tmp_path / "reader-ready"
    writer_done = tmp_path / "writer-done"
    process = get_context("spawn").Process(
        target=_crash_reader_while_second_reader_survives,
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
        assert changed.memory_id == created.memory_id
        assert changed.revision == 2
        writer_done.touch()
        process.join(timeout=30)
        if process.is_alive():
            process.terminate()
            process.join(timeout=5)
        assert process.exitcode == 0

        # The crashed child released only its own lock. The surviving reader
        # still observes the old row/event prefix after the independent commit.
        assert _snapshot(keeper) == ((1, "before"), [("create", 1)])
        with closing(sqlite3.connect(database, timeout=0.2)) as checkpoint:
            blocked = checkpoint.execute(
                "PRAGMA wal_checkpoint(TRUNCATE)"
            ).fetchone()
        assert blocked is not None
        assert blocked[0] == 1 or blocked[1] != blocked[2]

        keeper.rollback()
        keeper.close()

        # Once the final reader closes, a cold managed store must recover the
        # committed pair and a TRUNCATE checkpoint must finish without a busy
        # reader. A stale generation token remains a conflict, not a retry.
        cold = SQLiteMemoryStore(database, clock_ms=lambda: 300)
        assert cold.get(created.memory_id, scope) == changed
        assert [
            (event.event_id, event.operation, event.revision)
            for event in cold.events(scope)
        ] == [(1, "create", 1), (2, "update", 2)]
        with closing(sqlite3.connect(database, timeout=10)) as checkpoint:
            result = checkpoint.execute(
                "PRAGMA wal_checkpoint(TRUNCATE)"
            ).fetchone()
            assert result is not None
            assert result[0] == 0
            assert result[1] == result[2]
            assert checkpoint.execute("PRAGMA quick_check").fetchone() == ("ok",)

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
        writer_done.touch()
        if process.is_alive():
            process.terminate()
            process.join(timeout=5)
        if not keeper.in_transaction:
            keeper.close()
        else:
            keeper.rollback()
            keeper.close()
