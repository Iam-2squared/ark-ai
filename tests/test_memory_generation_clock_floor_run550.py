"""Memory generation ABA review must not bless regressed local event clocks."""

from __future__ import annotations

import sqlite3

import pytest

from ark.memory import MemoryScope, MemoryWrite, SQLiteMemoryStore
from ark.memory.cas_generation_review import (
    MemoryGenerationReviewRejected,
    review_memory_revision_reuse,
)


def make_store(tmp_path):
    clock = [1_000]
    store = SQLiteMemoryStore(
        tmp_path / "clock-history.sqlite",
        clock_ms=lambda: clock[0],
    )
    scope = MemoryScope("synthetic-owner", "clock")
    return clock, store, scope


def put(store, scope, content, revision=0):
    return store.put(
        MemoryWrite(scope, "source", content), expected_revision=revision,
    )


def review(store, scope, expected):
    return review_memory_revision_reuse(
        store, scope, "source", expected_revision=expected,
    )


def test_backdated_latest_update_with_row_aligned_clock_is_rejected(tmp_path):
    clock, store, scope = make_store(tmp_path)
    first = put(store, scope, "first")
    clock[0] = 2_000
    put(store, scope, "second", first.revision)
    with sqlite3.connect(store.path) as conn:
        conn.execute(
            "UPDATE memory_events SET occurred_at_ms=500 "
            "WHERE memory_id=? AND operation='update'",
            (first.memory_id,),
        )
        conn.execute(
            "UPDATE memories SET updated_at_ms=500 WHERE memory_id=?",
            (first.memory_id,),
        )
    with pytest.raises(MemoryGenerationReviewRejected, match="clock regressed"):
        review(store, scope, 2)


def test_backdated_middle_update_is_rejected_even_if_final_row_is_valid(tmp_path):
    clock, store, scope = make_store(tmp_path)
    first = put(store, scope, "first")
    clock[0] = 2_000
    second = put(store, scope, "second", first.revision)
    clock[0] = 3_000
    put(store, scope, "third", second.revision)
    with sqlite3.connect(store.path) as conn:
        conn.execute(
            "UPDATE memory_events SET occurred_at_ms=500 "
            "WHERE memory_id=? AND operation='update' AND revision=2",
            (first.memory_id,),
        )
    with pytest.raises(MemoryGenerationReviewRejected, match="clock regressed"):
        review(store, scope, 3)


def test_backdated_delete_before_recreate_is_rejected(tmp_path):
    clock, store, scope = make_store(tmp_path)
    first = put(store, scope, "first")
    clock[0] = 2_000
    store.delete(first.memory_id, scope, expected_revision=1)
    clock[0] = 3_000
    renewed = put(store, scope, "new generation")
    assert renewed.revision == 1
    with sqlite3.connect(store.path) as conn:
        conn.execute(
            "UPDATE memory_events SET occurred_at_ms=500 "
            "WHERE memory_id=? AND operation='delete'",
            (first.memory_id,),
        )
    with pytest.raises(MemoryGenerationReviewRejected, match="clock regressed"):
        review(store, scope, 1)


def test_identical_timestamps_are_allowed_without_attested_time(tmp_path):
    _, store, scope = make_store(tmp_path)
    first = put(store, scope, "initial")
    second = put(store, scope, "next", first.revision)
    report = review(store, scope, second.revision)
    assert report.event_count == 2
    assert report.live_revision == 2
    assert report.generation_authenticated is False
    assert report.write_authorized is False
