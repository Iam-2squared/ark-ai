"""Run1283: scoped expiry row/event deletion survives post-COMMIT process exit."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

from ark.memory import MemoryScope, MemoryWrite, SQLiteMemoryStore

_CHILD = r"""
import os
import sqlite3
import sys
from pathlib import Path

from ark.memory import MemoryScope, SQLiteMemoryStore

path = Path(sys.argv[1])
scope = MemoryScope("run1283-owner", "private")
store = SQLiteMemoryStore(path, clock_ms=lambda: 20)
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
            # The row deletion and matching event are committed together.
            # Exit before purge_expired can return its local count.
            os._exit(76)
        return result


def controlled_connect(database, *args, **kwargs):
    connection = native_connect(database, *args, **kwargs)
    if database == target_uri:
        return ExitAfterCommit(connection)
    return connection


sqlite3.connect = controlled_connect
store.purge_expired(scope=scope, limit=1)
os._exit(77)
"""


def test_scoped_expiry_row_and_event_survive_hard_exit_after_commit(
    tmp_path: Path,
) -> None:
    path = tmp_path / "memory-purge-native-commit-hard-exit.sqlite3"
    scope = MemoryScope("run1283-owner", "private")
    foreign = MemoryScope("run1283-owner", "other")
    writer = SQLiteMemoryStore(path, clock_ms=lambda: 10)
    expired = writer.put(
        MemoryWrite(scope, "expired-source", "expired-content", expires_at_ms=20),
    )
    live = writer.put(
        MemoryWrite(scope, "live-source", "live-content", expires_at_ms=200),
    )
    foreign_expired = writer.put(
        MemoryWrite(foreign, "foreign-source", "foreign-expired", expires_at_ms=20),
    )

    child = subprocess.run(
        [sys.executable, "-c", _CHILD, str(path)],
        capture_output=True,
        text=True,
        timeout=45,
        check=False,
    )
    assert child.returncode == 76, child.stdout + child.stderr

    cold = SQLiteMemoryStore(path, clock_ms=lambda: 21)
    assert cold.get(expired.memory_id, scope, include_expired=True) is None
    recovered_live = cold.get(live.memory_id, scope, include_expired=True)
    recovered_foreign = cold.get(
        foreign_expired.memory_id, foreign, include_expired=True,
    )
    assert recovered_live is not None
    assert recovered_live.content == "live-content"
    assert recovered_foreign is not None
    assert recovered_foreign.content == "foreign-expired"

    scoped_events = cold.events(scope)
    assert [
        (event.memory_id, event.operation, event.revision)
        for event in scoped_events
    ] == [
        (expired.memory_id, "create", 1),
        (live.memory_id, "create", 1),
        (expired.memory_id, "expire", 1),
    ]
    assert [
        (event.memory_id, event.operation)
        for event in cold.events(foreign)
    ] == [(foreign_expired.memory_id, "create")]

    # A cold retry sees no due target row and must not append a duplicate event.
    assert cold.purge_expired(scope=scope, limit=1) == 0
    assert tuple(cold.events(scope)) == tuple(scoped_events)
