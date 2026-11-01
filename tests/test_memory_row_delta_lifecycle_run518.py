"""Retained row snapshots independently check complete SQLite event lifecycles.

This does not prove original writer identity, consent, safe disclosure or
cross-store atomicity. All rows and events are local synthetic fixtures.
"""

from __future__ import annotations

import sqlite3
from pathlib import Path

import pytest

import ark.memory.sqlite_retained_row_delta_review as delta
from ark.memory import MemoryScope, MemoryWrite, SQLiteMemoryStore


def _fixture(tmp_path: Path):
    store = SQLiteMemoryStore(
        tmp_path / "local-memory.sqlite3", clock_ms=lambda: 1500,
    )
    scope = MemoryScope("owner", "notes")
    first = store.put(
        MemoryWrite(scope, "synthetic", "private fixture"),
        expected_revision=0,
    )
    return store, scope, first


@pytest.mark.parametrize("mutation", (
    "live_revision", "silent_delete", "missing_create_event",
    "duplicate_create_event", "invalid_update_event",
    "terminal_event_with_live_row", "event_scope_swap",
))
def test_invalid_live_row_or_event_lifecycle_is_not_new_valid_baseline(
    tmp_path: Path, mutation: str,
) -> None:
    store, scope, first = _fixture(tmp_path)
    retained = delta.capture_local_memory_row_delta(store)
    with sqlite3.connect(store.path) as conn:
        if mutation == "live_revision":
            conn.execute(
                "UPDATE memories SET revision=2 WHERE memory_id=?",
                (first.memory_id,),
            )
        elif mutation == "silent_delete":
            conn.execute(
                "DELETE FROM memories WHERE memory_id=?", (first.memory_id,),
            )
        elif mutation == "missing_create_event":
            conn.execute(
                "DELETE FROM memory_events WHERE memory_id=?", (first.memory_id,),
            )
        else:
            owner = "intruder" if mutation == "event_scope_swap" else scope.owner_id
            operation = (
                "create" if mutation == "duplicate_create_event"
                else "delete" if mutation == "terminal_event_with_live_row"
                else "update"
            )
            revision = (
                1 if operation != "update"
                else 3 if mutation == "invalid_update_event" else 2
            )
            conn.execute(
                "INSERT INTO memory_events("
                "memory_id,owner_id,namespace,operation,revision,occurred_at_ms"
                ") VALUES(?,?,?,?,?,?)",
                (
                    first.memory_id, owner, scope.namespace,
                    operation, revision, 1501,
                ),
            )
    with pytest.raises(delta.MemoryRowDeltaRejected):
        delta.capture_local_memory_row_delta(store)
    with pytest.raises(delta.MemoryRowDeltaRejected):
        delta.review_retained_memory_row_delta(store, retained)


def test_valid_update_and_delete_lifecycles_keep_row_review_inert(
    tmp_path: Path,
) -> None:
    store, scope, first = _fixture(tmp_path)
    retained = delta.capture_local_memory_row_delta(store)
    updated = store.put(
        MemoryWrite(scope, "synthetic", "changed fixture"),
        expected_revision=1,
    )
    assert updated.revision == 2
    assert delta.review_retained_memory_row_delta(
        store, retained,
    ).explained_changes == 1
    assert store.delete(first.memory_id, scope, expected_revision=2)
    reviewed = delta.review_retained_memory_row_delta(store, retained)
    assert reviewed.current_rows == 0
    assert reviewed.writer_authenticated is False
    assert reviewed.disclosure_authorized is False
    assert reviewed.action_authorized is False


def test_valid_delete_then_recreation_stays_a_local_lifecycle(
    tmp_path: Path,
) -> None:
    store, scope, first = _fixture(tmp_path)
    assert store.delete(first.memory_id, scope, expected_revision=1)
    recreated = store.put(
        MemoryWrite(scope, "synthetic", "new local fixture"),
        expected_revision=0,
    )
    assert recreated.revision == 1
    retained = delta.capture_local_memory_row_delta(store)
    assert delta.review_retained_memory_row_delta(
        store, retained,
    ).explained_changes == 0
