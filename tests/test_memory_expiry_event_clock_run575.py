"""Read-only expiry previews reject backward per-memory event clocks.

These are synthetic, manually mutated SQLite fixtures. Local timestamps are
not trusted time, physical deletion evidence, or consent to purge anything.
"""

from __future__ import annotations

import sqlite3

import pytest

from ark.memory import MemoryScope, MemoryWrite, SQLiteMemoryStore
from ark.memory.expiry_candidate_preview import (
    MemoryExpiryPreviewRejected,
    review_memory_expiry_candidates,
)


def _store(tmp_path, timestamps):
    times = iter(timestamps)
    store = SQLiteMemoryStore(
        tmp_path / "expiry-temporal.sqlite3",
        clock_ms=lambda: next(times),
    )
    scope = MemoryScope("synthetic-owner", "expiring")
    return store, scope


@pytest.mark.parametrize("tamper_revision", (2, 3))
def test_intermediate_update_regression_rejected_even_when_latest_row_matches(
    tmp_path, tamper_revision,
):
    store, scope = _store(tmp_path, (1000, 1500, 2000))
    first = store.put(MemoryWrite(scope, "sample", "one", expires_at_ms=500))
    store.put(
        MemoryWrite(scope, "sample", "two", expires_at_ms=500),
        expected_revision=1,
    )
    store.put(
        MemoryWrite(scope, "sample", "three", expires_at_ms=500),
        expected_revision=2,
    )
    with sqlite3.connect(store.path) as conn:
        conn.execute(
            "UPDATE memory_events SET occurred_at_ms=? "
            "WHERE memory_id=? AND operation='update' AND revision=?",
            (900 if tamper_revision == 2 else 1200,
             first.memory_id, tamper_revision),
        )
        if tamper_revision == 3:
            # Make the final row agree with the forged last event: it is
            # still invalid because it predates the earlier create event.
            conn.execute(
                "UPDATE memories SET updated_at_ms=1200 WHERE memory_id=?",
                (first.memory_id,),
            )
    with pytest.raises(MemoryExpiryPreviewRejected, match="clock regressed"):
        review_memory_expiry_candidates(store, scope, now_ms=3000)


def test_deleted_recreated_lifecycle_cannot_hide_backward_terminal_clock(tmp_path):
    store, scope = _store(tmp_path, (1000, 1600, 2500))
    first = store.put(MemoryWrite(scope, "sample", "old", expires_at_ms=500))
    assert store.delete(first.memory_id, scope, expected_revision=1)
    fresh = store.put(MemoryWrite(scope, "sample", "new", expires_at_ms=500))
    assert fresh.revision == 1
    with sqlite3.connect(store.path) as conn:
        conn.execute(
            "UPDATE memory_events SET occurred_at_ms=900 "
            "WHERE memory_id=? AND operation='delete'",
            (first.memory_id,),
        )
    with pytest.raises(MemoryExpiryPreviewRejected, match="clock regressed"):
        review_memory_expiry_candidates(store, scope, now_ms=3000)


def test_unchanged_equal_clock_recreation_is_valid_and_non_authorizing(tmp_path):
    store, scope = _store(tmp_path, (1000, 1000, 1000))
    first = store.put(MemoryWrite(scope, "sample", "old", expires_at_ms=500))
    assert store.delete(first.memory_id, scope, expected_revision=1)
    fresh = store.put(MemoryWrite(scope, "sample", "new", expires_at_ms=500))
    assert fresh.revision == 1
    result = review_memory_expiry_candidates(store, scope, now_ms=1000)
    assert result.candidate_count == 1
    assert result.has_more is False
    assert result.deletion_authorized is False
    assert result.trusted_clock_verified is False
