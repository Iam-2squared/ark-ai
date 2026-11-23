"""Run1147: Memory put COMMIT acknowledgement loss is manual-only UNKNOWN.

The subprocess installs a deterministic SQLite boundary before importing ARK.
It exercises both create/update and native rollback/native commit outcomes.
"""

from __future__ import annotations

import subprocess
import sys

import pytest


@pytest.mark.parametrize("operation", ("create", "update"))
@pytest.mark.parametrize("durable", (False, True))
def test_put_commit_ack_loss_requires_cold_readback_without_retry(
    tmp_path,
    operation: str,
    durable: bool,
) -> None:
    database = tmp_path / "memory-put-commit-unknown.sqlite3"
    script = r"""
import sqlite3
from pathlib import Path

DATABASE = Path(__DATABASE__)
OPERATION = __OPERATION__
DURABLE = __DURABLE__
TARGET_URI = DATABASE.resolve().as_uri() + "?mode=rw"
armed = False
commit_attempts = 0
native_connect = sqlite3.connect


class CommitBoundary:
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
        return self

    def __exit__(self, exc_type, exc, traceback):
        if exc_type is not None:
            self.connection.rollback()
            return False
        self.commit()
        return False

    def commit(self):
        global commit_attempts
        commit_attempts += 1
        if DURABLE:
            self.connection.commit()
        else:
            self.connection.rollback()
        raise sqlite3.OperationalError(
            "synthetic Memory put COMMIT acknowledgement lost"
        )

    def rollback(self):
        self.connection.rollback()

    def close(self):
        self.connection.close()


def controlled_connect(database, *args, **kwargs):
    connection = native_connect(database, *args, **kwargs)
    if armed and database == TARGET_URI:
        return CommitBoundary(connection)
    return connection


# Install the stable fixture factory before ARK imports SQLite dependencies.
sqlite3.connect = controlled_connect

from ark.memory import (
    MemoryConflictError,
    MemoryScope,
    MemoryWrite,
    SQLiteMemoryStore,
    deterministic_memory_id,
)

scope = MemoryScope("fixture-owner", "private")
store = SQLiteMemoryStore(DATABASE, clock_ms=lambda: 100)
if OPERATION == "update":
    initial = store.put(MemoryWrite(scope, "source", "before"))
    expected_revision = initial.revision
else:
    initial = None
    expected_revision = 0

memory_id = deterministic_memory_id(scope, "source")
proposal = MemoryWrite(
    scope,
    "source",
    "private_fixture_marker_after",
    {"fixture_label": "private_fixture_metadata"},
)
armed = True
try:
    store.put(proposal, expected_revision=expected_revision)
except sqlite3.OperationalError as exc:
    assert "COMMIT acknowledgement lost" in str(exc)
else:
    raise AssertionError("ambiguous Memory put COMMIT returned a record")
finally:
    armed = False

# Resolve the UNKNOWN outcome only by a cold read. No write is retried here.
assert commit_attempts == 1
cold = SQLiteMemoryStore(DATABASE, clock_ms=lambda: 200)
record = cold.get(memory_id, scope, include_expired=True)
events = cold.events(scope)

if OPERATION == "create":
    if DURABLE:
        assert record is not None
        assert record.revision == 1
        assert record.content == "private_fixture_marker_after"
        assert [(event.operation, event.revision) for event in events] == [
            ("create", 1),
        ]
        try:
            cold.put(proposal, expected_revision=0)
        except MemoryConflictError:
            pass
        else:
            raise AssertionError("durable create accepted its stale genesis CAS")
    else:
        assert record is None
        assert events == []
else:
    assert initial is not None
    if DURABLE:
        assert record is not None
        assert record.revision == 2
        assert record.content == "private_fixture_marker_after"
        assert [(event.operation, event.revision) for event in events] == [
            ("create", 1),
            ("update", 2),
        ]
        try:
            cold.put(proposal, expected_revision=1)
        except MemoryConflictError:
            pass
        else:
            raise AssertionError("durable update accepted its stale revision")
    else:
        assert record is not None
        assert record.revision == 1
        assert record.content == "before"
        assert [(event.operation, event.revision) for event in events] == [
            ("create", 1),
        ]

assert "private_fixture_marker_after" not in repr(events)
assert "private_fixture_metadata" not in repr(events)
assert commit_attempts == 1
"""
    script = (
        script
        .replace("__DATABASE__", repr(str(database)))
        .replace("__OPERATION__", repr(operation))
        .replace("__DURABLE__", repr(durable))
    )
    result = subprocess.run(
        [sys.executable, "-c", script],
        capture_output=True,
        text=True,
        timeout=90,
        check=False,
    )
    assert result.returncode == 0, result.stdout + result.stderr
