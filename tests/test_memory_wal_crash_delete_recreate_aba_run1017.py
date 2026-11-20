"""Run1017: Memory WAL reader crash cannot erase a delete/recreate ABA fence."""

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


def _snapshot(connection: sqlite3.Connection):
    row = connection.execute(
        "SELECT revision,content FROM memories "
        "WHERE owner_id=? AND namespace=? AND source_id=?",
        ("run1017-reader-owner", "private", "source"),
    ).fetchone()
    events = connection.execute(
        "SELECT event_id,operation,revision FROM memory_events ORDER BY event_id"
    ).fetchall()
    return row, events


def _crash_reader(
    database: str, ready: str, writer_done: str, reader_mode: str,
) -> None:
    path = Path(database)
    target = path.as_uri() + "?mode=ro" if reader_mode == "ro" else str(path)
    connection = sqlite3.connect(
        target, uri=reader_mode == "ro", timeout=10, isolation_level=None,
    )
    connection.execute("BEGIN")
    before = ((1, "before"), [(1, "create", 1)])
    assert _snapshot(connection) == before
    Path(ready).touch()
    deadline = time.monotonic() + 25
    while not Path(writer_done).exists():
        if time.monotonic() >= deadline:
            os._exit(2)
        time.sleep(0.02)

    # The writer has deleted and recreated the same deterministic Memory ID.
    # This reader must retain its original SQLite snapshot, then die without
    # closing its transaction so the independent keeper remains authoritative.
    assert _snapshot(connection) == before
    os._exit(0)


def _await_marker(path: Path, process) -> None:
    deadline = time.monotonic() + 25
    while not path.exists():
        if process.exitcode is not None:
            raise AssertionError("WAL reader exited before its barrier")
        if time.monotonic() >= deadline:
            raise AssertionError("WAL reader barrier timed out")
        time.sleep(0.02)


@pytest.mark.parametrize("reader_mode", ("ro", "rw"))
def test_wal_reader_crash_and_last_close_preserve_memory_delete_recreate_aba(
    tmp_path: Path, reader_mode: str,
) -> None:
    database = tmp_path / "memory-delete-recreate-aba.sqlite3"
    scope = MemoryScope("run1017-reader-owner", "private")
    initial = SQLiteMemoryStore(database, clock_ms=lambda: 100)
    created = initial.put(MemoryWrite(scope, "source", "before"))
    stale = observe_memory_generation_for_cas(initial, scope, "source")

    # Keep one parent reader alive after the child exits. It must keep the old
    # snapshot pinned and prevent a completed TRUNCATE checkpoint.
    keeper = sqlite3.connect(database, timeout=10, isolation_level=None)
    keeper_open = True
    keeper.execute("PRAGMA query_only=ON")
    keeper.execute("BEGIN")
    before = ((1, "before"), [(1, "create", 1)])
    assert _snapshot(keeper) == before

    ready = tmp_path / "reader-ready"
    writer_done = tmp_path / "writer-done"
    process = get_context("spawn").Process(
        target=_crash_reader,
        args=(str(database), str(ready), str(writer_done), reader_mode),
    )
    process.start()
    try:
        _await_marker(ready, process)

        assert initial.delete(created.memory_id, scope, expected_revision=1) is True
        recreated = initial.put(MemoryWrite(scope, "source", "after-recreate"))
        assert recreated.memory_id == created.memory_id
        assert recreated.revision == 1
        writer_done.touch()

        process.join(timeout=30)
        if process.is_alive():
            process.terminate()
            process.join(timeout=5)
        assert process.exitcode == 0
        assert _snapshot(keeper) == before

        with closing(sqlite3.connect(database, timeout=0.2)) as checkpoint:
            blocked = checkpoint.execute(
                "PRAGMA wal_checkpoint(TRUNCATE)"
            ).fetchone()
        assert blocked is not None
        assert blocked[0] == 1 or blocked[1] != blocked[2]

        keeper.rollback()
        keeper.close()
        keeper_open = False

        cold = SQLiteMemoryStore(database, clock_ms=lambda: 300)
        assert cold.get(created.memory_id, scope) == recreated
        expected_events = [
            (1, "create", 1), (2, "delete", 1), (3, "create", 1),
        ]
        assert [
            (event.event_id, event.operation, event.revision)
            for event in cold.events(scope)
        ] == expected_events

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
                cold, MemoryWrite(scope, "source", "stale replay"),
                retained=stale,
            )
        assert cold.get(created.memory_id, scope) == recreated
        assert [
            (event.event_id, event.operation, event.revision)
            for event in cold.events(scope)
        ] == expected_events

        fresh = observe_memory_generation_for_cas(cold, scope, "source")
        updated = generation_fenced_memory_update(
            SQLiteMemoryStore(database, clock_ms=lambda: 400),
            MemoryWrite(scope, "source", "new lifetime updated"),
            retained=fresh,
        )
        assert updated.memory_id == created.memory_id
        assert updated.revision == 2
        assert updated.content == "new lifetime updated"

        reopened = SQLiteMemoryStore(database, clock_ms=lambda: 500)
        assert reopened.get(created.memory_id, scope) == updated
        assert [
            (event.event_id, event.operation, event.revision)
            for event in reopened.events(scope)
        ] == expected_events + [(4, "update", 2)]
    finally:
        writer_done.touch()
        if process.is_alive():
            process.terminate()
            process.join(timeout=5)
        if keeper_open:
            if keeper.in_transaction:
                keeper.rollback()
            keeper.close()
