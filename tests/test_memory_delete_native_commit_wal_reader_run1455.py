"""Run1455: a delete committed before process exit survives a pinned WAL reader.

Synthetic local SQLite only. This does not establish power-loss durability,
physical erasure, independent custody, trusted time, consent, or external effects.
"""

from __future__ import annotations

import sqlite3
import subprocess
import sys
from contextlib import closing
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
scope = MemoryScope("run1455-owner", "private")
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
            # Native COMMIT returned. Exit before delete() can validate the
            # source path, close the handle, or return its receipt.
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


def _snapshot(connection: sqlite3.Connection):
    row = connection.execute(
        "SELECT memory_id,revision,content FROM memories "
        "WHERE owner_id=? AND namespace=? AND source_id=?",
        ("run1455-owner", "private", "target-source"),
    ).fetchone()
    events = connection.execute(
        "SELECT event_id,memory_id,operation,revision FROM memory_events "
        "WHERE owner_id=? AND namespace=? ORDER BY event_id",
        ("run1455-owner", "private"),
    ).fetchall()
    return row, events


def test_delete_native_commit_survives_process_exit_and_pinned_wal_reader(
    tmp_path: Path,
) -> None:
    database = tmp_path / "memory-delete-native-commit-wal-reader.sqlite3"
    scope = MemoryScope("run1455-owner", "private")
    writer = SQLiteMemoryStore(database, clock_ms=lambda: 100)
    target = writer.put(
        MemoryWrite(scope, "target-source", "private-delete-target"),
    )
    unrelated = writer.put(
        MemoryWrite(scope, "unrelated-source", "unrelated-private-row"),
    )
    stale = observe_memory_generation_for_cas(writer, scope, "target-source")

    # Pin a pre-delete WAL snapshot in a different process lifetime. The child
    # must commit while this reader remains open; the old snapshot stays visible
    # until the keeper releases it.
    keeper = sqlite3.connect(database, timeout=10, isolation_level=None)
    keeper_open = True
    keeper.execute("PRAGMA query_only=ON")
    keeper.execute("BEGIN")
    before = (
        (target.memory_id, 1, "private-delete-target"),
        [
            (1, target.memory_id, "create", 1),
            (2, unrelated.memory_id, "create", 1),
        ],
    )
    assert _snapshot(keeper) == before

    child = subprocess.run(
        [sys.executable, "-c", _CHILD, str(database), target.memory_id],
        capture_output=True,
        text=True,
        timeout=45,
        check=False,
    )
    assert child.returncode == 78, child.stdout + child.stderr

    # The pinned reader still sees its old snapshot although the delete's
    # native COMMIT returned and the writer process has terminated.
    assert _snapshot(keeper) == before
    with closing(sqlite3.connect(database, timeout=0.2)) as checkpoint:
        blocked = checkpoint.execute("PRAGMA wal_checkpoint(TRUNCATE)").fetchone()
    assert blocked is not None
    assert blocked[0] == 1 or blocked[1] != blocked[2]

    keeper.rollback()
    keeper.close()
    keeper_open = False

    cold = SQLiteMemoryStore(database, clock_ms=lambda: 300)
    assert cold.get(target.memory_id, scope, include_expired=True) is None
    assert cold.get(unrelated.memory_id, scope, include_expired=True) == unrelated
    committed_events = tuple(cold.events(scope))
    expected_events = (
        (1, target.memory_id, "create", 1),
        (2, unrelated.memory_id, "create", 1),
        (3, target.memory_id, "delete", 1),
    )
    assert tuple(
        (event.event_id, event.memory_id, event.operation, event.revision)
        for event in committed_events
    ) == expected_events
    assert "private-delete-target" not in repr(committed_events)
    assert "unrelated-private-row" not in repr(committed_events)

    # The old generation is still stale; a delete retry is a no-op and neither
    # path can append a duplicate event or recreate the deterministic identity.
    assert cold.delete(target.memory_id, scope, expected_revision=1) is False
    with pytest.raises((MemoryConflictError, MemoryGenerationCASRejected)):
        generation_fenced_memory_update(
            cold,
            MemoryWrite(scope, "target-source", "must-not-resurrect"),
            retained=stale,
        )
    assert cold.get(target.memory_id, scope, include_expired=True) is None
    assert tuple(cold.events(scope)) == committed_events

    with closing(sqlite3.connect(database, timeout=10)) as connection:
        assert connection.execute("PRAGMA quick_check").fetchone() == ("ok",)
        rows = connection.execute(
            "SELECT memory_id,content,revision FROM memories ORDER BY memory_id",
        ).fetchall()
        assert rows == [(unrelated.memory_id, "unrelated-private-row", 1)]
        events = connection.execute(
            "SELECT event_id,memory_id,operation,revision "
            "FROM memory_events ORDER BY event_id",
        ).fetchall()
        assert events == list(expected_events)
        checkpoint = connection.execute("PRAGMA wal_checkpoint(TRUNCATE)").fetchone()
        assert checkpoint is not None
        assert checkpoint[0] == 0
        assert checkpoint[1] == checkpoint[2]

    reopened = SQLiteMemoryStore(database, clock_ms=lambda: 400)
    assert reopened.get(target.memory_id, scope, include_expired=True) is None
    assert reopened.get(unrelated.memory_id, scope, include_expired=True) == unrelated
    assert tuple(reopened.events(scope)) == committed_events
    if keeper_open:
        keeper.rollback()
        keeper.close()
