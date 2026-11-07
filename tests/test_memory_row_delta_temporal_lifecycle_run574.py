"""Retained Memory row review binds SQLite row clocks to event lifecycles.

All rows and rewrites here are disposable synthetic fixtures. Event timestamps
are local clock observations, NOT trusted time or proof of writer identity.
"""

from __future__ import annotations

import sqlite3

import pytest

import ark.memory.sqlite_retained_row_delta_review as review
from ark.memory import MemoryScope, MemoryWrite, SQLiteMemoryStore


def _store(tmp_path, times=(1000, 1500, 2000, 2500)):
    ticks = iter(times)
    store = SQLiteMemoryStore(
        tmp_path / "synthetic-temporal.sqlite3",
        clock_ms=lambda: next(ticks),
    )
    scope = MemoryScope("fixture-owner", "notes")
    first = store.put(
        MemoryWrite(scope, "synthetic", "original test text"),
        expected_revision=0,
    )
    return store, scope, first


@pytest.mark.parametrize(
    ("field", "value"),
    (
        ("created_at_ms", 999),
        ("updated_at_ms", 1001),
    ),
)
def test_initial_capture_rejects_row_timestamp_without_matching_event(
    tmp_path, field, value,
):
    store, _, first = _store(tmp_path)
    with sqlite3.connect(store.path) as conn:
        conn.execute(
            f"UPDATE memories SET {field}=? WHERE memory_id=?",
            (value, first.memory_id),
        )
    with pytest.raises(review.MemoryRowDeltaRejected, match="timestamps"):
        review.capture_local_memory_row_delta(store)


def test_update_clock_regression_rejected_even_if_row_matches_forged_event(tmp_path):
    store, scope, first = _store(tmp_path)
    store.put(
        MemoryWrite(scope, "synthetic", "changed test text"),
        expected_revision=1,
    )
    with sqlite3.connect(store.path) as conn:
        conn.execute(
            "UPDATE memory_events SET occurred_at_ms=999 "
            "WHERE memory_id=? AND operation='update'",
            (first.memory_id,),
        )
        conn.execute(
            "UPDATE memories SET updated_at_ms=999 WHERE memory_id=?",
            (first.memory_id,),
        )
    with pytest.raises(review.MemoryRowDeltaRejected, match="clock regressed"):
        review.capture_local_memory_row_delta(store)


def test_non_regressing_update_and_deleted_recreated_lifetime_stay_valid(tmp_path):
    store, scope, first = _store(tmp_path)
    baseline = review.capture_local_memory_row_delta(store)
    store.put(
        MemoryWrite(scope, "synthetic", "updated test text"),
        expected_revision=1,
    )
    assert review.review_retained_memory_row_delta(
        store, baseline,
    ).explained_changes == 1
    assert store.delete(first.memory_id, scope, expected_revision=2)
    recreated = store.put(
        MemoryWrite(scope, "synthetic", "recreated test text"),
        expected_revision=0,
    )
    assert recreated.revision == 1
    witness = review.capture_local_memory_row_delta(store)
    assert witness.event_count == 4
    assert review.review_retained_memory_row_delta(
        store, witness,
    ).explained_changes == 0


def test_equal_per_memory_timestamps_are_allowed_by_local_clock_review(tmp_path):
    store, scope, _ = _store(tmp_path, times=(1000, 1000))
    store.put(
        MemoryWrite(scope, "synthetic", "updated same-clock text"),
        expected_revision=1,
    )
    baseline = review.capture_local_memory_row_delta(store)
    assert baseline.event_count == 2
    assert review.review_retained_memory_row_delta(
        store, baseline,
    ).appended_events == 0


def test_unrelated_scope_clock_may_precede_another_scopes_clock(tmp_path):
    store, scope, _ = _store(tmp_path, times=(2000, 1000))
    store.put(
        MemoryWrite(scope, "another-source", "independent clock fixture"),
        expected_revision=0,
    )
    result = review.capture_local_memory_row_delta(store)
    assert len(result.rows) == 2
    assert result.event_count == 2
    assert result.disclosure_authorized is False
