"""Run1448: Memory delete row/event pair survives exit at native COMMIT return.

The fixture uses a disposable local SQLite database and synthetic private values.
It does not establish physical erasure, independent custody, power-loss
durability, trusted time, consent, or exactly-once behavior outside SQLite.
"""

from __future__ import annotations

import sqlite3
import subprocess
import sys
from pathlib import Path

import pytest

from ark.memory import MemoryConflictError, MemoryScope, MemoryWrite, SQLiteMemoryStore
from ark.memory.generation_fenced_cas import (
    MemoryGenerationCASRejected,
    generation_fenced_memory_update,
    observe_memory_generation_for_cas,
)

_CHILD = r"""
import os
import sqlite3
import sys
from pathlib import Path

from ark.memory import MemoryScope, SQLiteMemoryStore

database = Path(sys.argv[1])
memory_id = sys.argv[2]
scope = MemoryScope("run1448-owner", "private")
store = SQLiteMemoryStore(database, clock_ms=lambda: 200)
target_uri = database.resolve().as_uri() + "?mode=rw"
native_connect = sqlite3.connect


class ExitAfterNativeCommit:
    def __init__(self, connection):
        object.__setattr__(self, "connection", connection)

    def __getattr__(self, name):
        return getattr(self.connection, name)

    def __setattr__(self, name, value):
        if name == "connection":
            object.__setattr__(self, name, value)
        else:
            setattr(self.connection, name, value)

    def __enter__(self):
        self.connection.__enter__()
        return self

    def __exit__(self, exc_type, exc, traceback):
        result = self.connection.__exit__(exc_type, exc, traceback)
        if exc_type is None:
            # Native SQLite COMMIT has returned. Exit before delete() can
            # perform post-COMMIT validation, close the handle or return.
            os._exit(78)
        return result

    def close(self):
        self.connection.close()


def controlled_connect(database_arg, *args, **kwargs):
    connection = native_connect(database_arg, *args, **kwargs)
    if database_arg == target_uri:
        return ExitAfterNativeCommit(connection)
    return connection


sqlite3.connect = controlled_connect
store.delete(memory_id, scope, expected_revision=1)
os._exit(79)
"""


def test_delete_row_and_event_survive_hard_exit_after_native_commit(
    tmp_path: Path,
) -> None:
    database = tmp_path / "memory-delete-native-commit.sqlite3"
    scope = MemoryScope("run1448-owner", "private")
    writer = SQLiteMemoryStore(database, clock_ms=lambda: 100)
    target = writer.put(MemoryWrite(scope, "target-source", "private-delete-target"))
    unrelated = writer.put(
        MemoryWrite(scope, "unrelated-source", "unrelated-private-row"),
    )
    stale = observe_memory_generation_for_cas(writer, scope, "target-source")

    child = subprocess.run(
        [sys.executable, "-c", _CHILD, str(database), target.memory_id],
        capture_output=True,
        text=True,
        timeout=45,
        check=False,
    )
    assert child.returncode == 78, child.stdout + child.stderr

    cold = SQLiteMemoryStore(database, clock_ms=lambda: 300)
    assert cold.get(target.memory_id, scope, include_expired=True) is None
    recovered_unrelated = cold.get(
        unrelated.memory_id, scope, include_expired=True,
    )
    assert recovered_unrelated == unrelated

    committed_events = tuple(cold.events(scope))
    assert [
        (event.event_id, event.memory_id, event.operation, event.revision)
        for event in committed_events
    ] == [
        (1, target.memory_id, "create", 1),
        (2, unrelated.memory_id, "create", 1),
        (3, target.memory_id, "delete", 1),
    ]
    assert "private-delete-target" not in repr(committed_events)
    assert "unrelated-private-row" not in repr(committed_events)

    # A blind retry is a no-op and cannot append a second delete event.
    assert cold.delete(target.memory_id, scope, expected_revision=1) is False
    assert tuple(cold.events(scope)) == committed_events

    # The pre-delete generation cannot recreate the deleted deterministic ID.
    with pytest.raises((MemoryConflictError, MemoryGenerationCASRejected)):
        generation_fenced_memory_update(
            cold,
            MemoryWrite(scope, "target-source", "must-not-resurrect"),
            retained=stale,
        )
    assert cold.get(target.memory_id, scope, include_expired=True) is None
    assert tuple(cold.events(scope)) == committed_events

    with sqlite3.connect(database) as connection:
        assert connection.execute("PRAGMA quick_check").fetchone() == ("ok",)
        rows = connection.execute(
            "SELECT memory_id,content,revision FROM memories ORDER BY memory_id",
        ).fetchall()
        assert rows == [(unrelated.memory_id, "unrelated-private-row", 1)]
        events = connection.execute(
            "SELECT event_id,memory_id,operation,revision "
            "FROM memory_events ORDER BY event_id",
        ).fetchall()
        assert events == [
            (1, target.memory_id, "create", 1),
            (2, unrelated.memory_id, "create", 1),
            (3, target.memory_id, "delete", 1),
        ]
