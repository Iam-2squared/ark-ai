"""SQLite WAL abrupt-process-exit atomicity, with no external effects.

Each case deliberately exits a spawned, isolated Python process while a local
SQLite transaction is open. An uncommitted row/event pair must not become a
partial history after crash recovery. These are synthetic local storage tests,
not an authenticated-writer or real-world exactly-once claim.
"""

from __future__ import annotations

import os
import sqlite3
from multiprocessing import get_context

import pytest

from ark.memory import MemoryScope, MemoryWrite, SQLiteMemoryStore
from ark.memory.generation_fenced_cas import (
    generation_fenced_memory_update,
    observe_memory_generation_for_cas,
)
from ark.memory.sqlite_store import deterministic_memory_id


def _crash_during_transaction(path: str, operation: str) -> None:
    # No Python exception/context manager exits or COMMIT are permitted here.
    # In particular, the matching event is deliberately staged but not durable.
    connection = sqlite3.connect(path, timeout=30, isolation_level=None)
    connection.execute("PRAGMA journal_mode=WAL")
    connection.execute("BEGIN IMMEDIATE")
    if operation == "update":
        connection.execute(
            "UPDATE memories SET content=?,content_sha256=?,revision=2 "
            "WHERE owner_id=? AND namespace=? AND source_id=?",
            ("uncommitted", "a" * 64, "wal-owner", "private", "seed"),
        )
        revision, kind = 2, "update"
        memory_id = deterministic_memory_id(MemoryScope("wal-owner", "private"), "seed")
    elif operation == "delete":
        memory_id = deterministic_memory_id(MemoryScope("wal-owner", "private"), "seed")
        connection.execute("DELETE FROM memories WHERE memory_id=?", (memory_id,))
        revision, kind = 1, "delete"
    else:
        memory_id = deterministic_memory_id(MemoryScope("wal-owner", "private"), "other")
        connection.execute(
            "INSERT INTO memories(memory_id,owner_id,namespace,source_id,"
            "content,metadata_json,content_sha256,created_at_ms,updated_at_ms,"
            "expires_at_ms,revision) VALUES(?,?,?,?,?,?,?,?,?,?,?)",
            (
                memory_id, "wal-owner", "private", "other", "uncommitted", "{}",
                "a" * 64, 401, 401, None, 1,
            ),
        )
        revision, kind = 1, "create"
    connection.execute(
        "INSERT INTO memory_events(memory_id,owner_id,namespace,operation,"
        "revision,occurred_at_ms) VALUES(?,?,?,?,?,?)",
        (memory_id, "wal-owner", "private", kind, revision, 401),
    )
    # Child intentionally loses both the transaction and response.
    os._exit(0)


@pytest.mark.parametrize("uncommitted_operation", ("update", "delete", "create"))
def test_abrupt_exit_rolls_back_both_row_and_event(
    tmp_path, uncommitted_operation,
):
    path = tmp_path / "abrupt-exit-memory.sqlite3"
    scope = MemoryScope("wal-owner", "private")
    first = SQLiteMemoryStore(path, clock_ms=lambda: 400)
    original = first.put(MemoryWrite(scope, "seed", "original"))
    before = observe_memory_generation_for_cas(first, scope, "seed")
    initial_events = tuple(first.events(scope))
    child = get_context("spawn").Process(
        target=_crash_during_transaction, args=(str(path), uncommitted_operation),
    )
    child.start()
    child.join(timeout=35)
    if child.is_alive():
        child.terminate()
        child.join(timeout=5)
    assert child.exitcode == 0

    reopened = SQLiteMemoryStore(path, clock_ms=lambda: 402)
    observed = reopened.get(original.memory_id, scope)
    assert observed is not None
    assert (observed.content, observed.revision) == ("original", 1)
    assert tuple(reopened.events(scope)) == initial_events
    if uncommitted_operation == "create":
        new_id = deterministic_memory_id(scope, "other")
        assert reopened.get(new_id, scope) is None
    fresh = observe_memory_generation_for_cas(reopened, scope, "seed")
    assert fresh == before
    # The aborted transaction does NOT consume the original CAS generation.
    updated = generation_fenced_memory_update(
        reopened, MemoryWrite(scope, "seed", "legitimate-retry"), retained=before,
    )
    assert updated.revision == 2
    assert reopened.get(original.memory_id, scope).content == "legitimate-retry"
    assert [event.operation for event in reopened.events(scope)] == [
        "create", "update",
    ]
