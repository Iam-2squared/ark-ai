"""Whole-store Memory history must agree with persisted lifetime timestamps.

A local audit of synthetic SQLite is not clock attestation, consent, or erasure.
"""

from __future__ import annotations

import sqlite3

import pytest

from ark.memory import MemoryScope, MemoryWrite, SQLiteMemoryStore
from ark.memory.sqlite_event_alignment import (
    MemoryEventAlignmentRejected,
    review_memory_event_alignment,
)


def _fixture(tmp_path):
    observed = {"ms": 1000}
    store = SQLiteMemoryStore(
        tmp_path / "memory.sqlite",
        clock_ms=lambda: observed["ms"],
    )
    scope = MemoryScope("synthetic-owner", "notes")
    first = store.put(MemoryWrite(scope, "source", "v1"))
    observed["ms"] = 2000
    second = store.put(
        MemoryWrite(scope, "source", "v2"),
        expected_revision=first.revision,
    )
    assert second.revision == 2
    return store, scope, observed, second


@pytest.mark.parametrize("target", (
    "row_created", "row_updated", "event_create", "event_update",
))
def test_full_audit_rejects_lifetime_time_drift(tmp_path, target):
    store, _, _, second = _fixture(tmp_path)
    assert review_memory_event_alignment(store).event_count == 2
    with sqlite3.connect(store.path) as conn:
        if target == "row_created":
            conn.execute(
                "UPDATE memories SET created_at_ms=1001 WHERE memory_id=?",
                (second.memory_id,),
            )
        elif target == "row_updated":
            conn.execute(
                "UPDATE memories SET updated_at_ms=2001 WHERE memory_id=?",
                (second.memory_id,),
            )
        elif target == "event_create":
            conn.execute(
                "UPDATE memory_events SET occurred_at_ms=1001 "
                "WHERE memory_id=? AND operation='create'",
                (second.memory_id,),
            )
        else:
            conn.execute(
                "UPDATE memory_events SET occurred_at_ms=2001 "
                "WHERE memory_id=? AND operation='update'",
                (second.memory_id,),
            )
    with pytest.raises(MemoryEventAlignmentRejected, match="row/time"):
        review_memory_event_alignment(store)
    # Read-only audit never rewrites or removes the live record.
    assert store.get(second.memory_id, second.scope, include_expired=True)


def test_delete_recreate_resets_created_at_to_current_cycle(tmp_path):
    store, scope, observed, second = _fixture(tmp_path)
    assert store.delete(second.memory_id, scope, expected_revision=2)
    observed["ms"] = 3000
    recreated = store.put(MemoryWrite(scope, "source", "recreated"))
    assert recreated.revision == 1
    assert recreated.created_at_ms == 3000
    report = review_memory_event_alignment(store)
    assert (report.row_count, report.event_count) == (1, 4)
    with sqlite3.connect(store.path) as conn:
        conn.execute(
            "UPDATE memories SET created_at_ms=1000 WHERE memory_id=?",
            (recreated.memory_id,),
        )
    with pytest.raises(MemoryEventAlignmentRejected, match="row/time"):
        review_memory_event_alignment(store)


def test_local_clock_does_not_need_to_be_monotonic(tmp_path):
    store, _, observed, second = _fixture(tmp_path)
    observed["ms"] = 500
    changed = store.put(
        MemoryWrite(second.scope, "source", "clock moved backward"),
        expected_revision=second.revision,
    )
    assert changed.updated_at_ms == 500
    assert review_memory_event_alignment(store).event_count == 3


def test_matching_local_rewrite_changes_untrusted_digest(tmp_path):
    store, _, _, second = _fixture(tmp_path)
    original = review_memory_event_alignment(store)
    with sqlite3.connect(store.path) as conn:
        conn.execute(
            "UPDATE memories SET updated_at_ms=3000 WHERE memory_id=?",
            (second.memory_id,),
        )
        conn.execute(
            "UPDATE memory_events SET occurred_at_ms=3000 "
            "WHERE memory_id=? AND operation='update'",
            (second.memory_id,),
        )
    modified = review_memory_event_alignment(store)
    assert modified.digest != original.digest
    assert modified.action_authorized is False
    assert modified.independently_authenticated is False
