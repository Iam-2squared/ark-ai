"""Run1242: a production Memory row/event pair survives post-COMMIT process exit."""

from __future__ import annotations

import sqlite3
import subprocess
import sys
from pathlib import Path

import pytest

from ark.memory import MemoryScope, MemoryWrite, SQLiteMemoryStore


_CHILD = r"""
import os
import sqlite3
import sys
from pathlib import Path

from ark.memory import MemoryScope, MemoryWrite, SQLiteMemoryStore

path = Path(sys.argv[1])
scope = MemoryScope("run1242-owner", "private")
store = SQLiteMemoryStore(path, clock_ms=lambda: 200)
target_uri = path.resolve().as_uri() + "?mode=rw"
native_connect = sqlite3.connect


class ExitAfterCommit:
    def __init__(self, connection):
        self.connection = connection

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
            # SQLite committed the row/event pair; skip close and Python return.
            os._exit(74)
        return result


def controlled_connect(database, *args, **kwargs):
    connection = native_connect(database, *args, **kwargs)
    if database == target_uri:
        return ExitAfterCommit(connection)
    return connection


sqlite3.connect = controlled_connect
store.put(
    MemoryWrite(
        scope,
        "source",
        "after",
        {"fixture_label": "private-metadata-after"},
    ),
    expected_revision=1,
)
os._exit(75)
"""


def test_put_row_and_event_survive_hard_exit_after_native_commit(
    tmp_path: Path,
) -> None:
    path = tmp_path / "memory-native-commit-hard-exit.sqlite3"
    scope = MemoryScope("run1242-owner", "private")
    writer = SQLiteMemoryStore(path, clock_ms=lambda: 100)
    original = writer.put(
        MemoryWrite(scope, "source", "before", {"fixture_label": "private-metadata-before"}),
    )

    child = subprocess.run(
        [sys.executable, "-c", _CHILD, str(path)],
        capture_output=True,
        text=True,
        timeout=45,
        check=False,
    )
    if child.returncode != 74:
        pytest.fail(child.stdout + child.stderr)

    cold = SQLiteMemoryStore(path, clock_ms=lambda: 300)
    recovered = cold.get(original.memory_id, scope)
    assert recovered is not None
    assert recovered.content == "after"
    assert recovered.metadata == {"fixture_label": "private-metadata-after"}
    assert recovered.revision == 2
    assert [
        (event.operation, event.revision, event.occurred_at_ms)
        for event in cold.events(scope)
    ] == [
        ("create", 1, 100),
        ("update", 2, 200),
    ]

    with sqlite3.connect(path) as connection:
        assert connection.execute("PRAGMA quick_check").fetchone() == ("ok",)
        assert connection.execute(
            "SELECT revision,content FROM memories WHERE memory_id=?",
            (original.memory_id,),
        ).fetchone() == (2, "after")
        assert connection.execute(
            "SELECT event_id,operation,revision FROM memory_events ORDER BY event_id"
        ).fetchall() == [(1, "create", 1), (2, "update", 2)]
