"""Aborted WAL transactions must not leak partial Memory row/event mutations.

All changes use disposable SQLite and a spawned interpreter. A local event
witness is not authenticated history, consent, or real action authorization.
"""

from __future__ import annotations

import hashlib
import os
import sqlite3
from multiprocessing import get_context

import pytest

from ark.memory import MemoryScope, MemoryWrite, SQLiteMemoryStore
from ark.memory.generation_fenced_cas import (
    generation_fenced_memory_update,
    observe_memory_generation_for_cas,
)
from ark.memory.sqlite_event_alignment import review_memory_event_alignment
from ark.memory.sqlite_event_prefix_review import capture_local_memory_event_prefix
from ark.memory.sqlite_retained_coherent_review import review_retained_coherent_memory
from ark.memory.sqlite_retained_row_delta_review import capture_local_memory_row_delta
from ark.memory.sqlite_store import deterministic_memory_id


def _abort_staged_change(path: str, stage: str) -> None:
    scope = MemoryScope("partial-wal-owner", "private")
    memory_id = deterministic_memory_id(scope, "seed")
    conn = sqlite3.connect(path, timeout=30, isolation_level=None)
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("BEGIN IMMEDIATE")

    def row() -> None:
        text = "uncommitted private replacement"
        conn.execute(
            "UPDATE memories SET content=?,content_sha256=?,revision=2 "
            "WHERE memory_id=?",
            (text, hashlib.sha256(text.encode()).hexdigest(), memory_id),
        )

    def event() -> None:
        conn.execute(
            "INSERT INTO memory_events(memory_id,owner_id,namespace,"
            "operation,revision,occurred_at_ms) VALUES(?,?,?,?,?,?)",
            (memory_id, scope.owner_id, scope.namespace, "update", 2, 501),
        )

    if stage == "row_only":
        row()
    elif stage == "event_only":
        event()
    elif stage == "row_then_event":
        row()
        event()
    elif stage == "event_then_row":
        event()
        row()
    else:
        raise AssertionError("invalid local crash fixture")
    os._exit(0)  # No COMMIT, rollback callback, or success response.


@pytest.mark.parametrize(
    "stage", ("row_only", "event_only", "row_then_event", "event_then_row"),
)
def test_partial_uncommitted_wal_stages_rollback_after_process_exit(tmp_path, stage):
    path = tmp_path / "partial-wal.sqlite3"
    scope = MemoryScope("partial-wal-owner", "private")
    original_store = SQLiteMemoryStore(path, clock_ms=lambda: 500)
    original = original_store.put(MemoryWrite(scope, "seed", "durable original"))
    prefix = capture_local_memory_event_prefix(original_store)
    alignment = review_memory_event_alignment(original_store)
    row_witness = capture_local_memory_row_delta(original_store)
    token = observe_memory_generation_for_cas(original_store, scope, "seed")
    original_events = tuple(original_store.events(scope))

    child = get_context("spawn").Process(
        target=_abort_staged_change, args=(str(path), stage),
    )
    child.start()
    child.join(timeout=35)
    if child.is_alive():
        child.terminate()
        child.join(timeout=5)
    assert child.exitcode == 0

    cold = SQLiteMemoryStore(path, clock_ms=lambda: 502)
    persisted = cold.get(original.memory_id, scope)
    assert persisted is not None
    assert (persisted.content, persisted.revision) == ("durable original", 1)
    assert tuple(cold.events(scope)) == original_events
    reviewed = review_retained_coherent_memory(
        cold, prefix, alignment, prior_rows=row_witness,
    )
    assert reviewed.status == "UNCHANGED_LOCAL_HISTORY"
    assert (reviewed.previous_event_count, reviewed.current_event_count) == (1, 1)
    assert reviewed.retained_row_delta_checked is True
    assert reviewed.historical_writer_authenticated is False
    assert reviewed.action_authorized is False
    assert reviewed.cross_store_atomicity_proven is False

    committed = generation_fenced_memory_update(
        cold, MemoryWrite(scope, "seed", "manual committed update"), retained=token,
    )
    assert committed.revision == 2
    assert [e.operation for e in cold.events(scope)] == ["create", "update"]
