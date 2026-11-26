"""Read-only coherent Memory timestamp checks against each OWN event lifecycle.

A different owner's valid append must not excuse an existing row's timestamp
rewrite when the optional retained-row witness is absent. These are local,
unauthenticated, disposable SQLite fixtures; no real effects or authorizations.
"""

from __future__ import annotations

import sqlite3
from contextlib import closing

import pytest

from ark.memory import MemoryScope, MemoryWrite, SQLiteMemoryStore
from ark.memory.sqlite_event_alignment import review_memory_event_alignment
from ark.memory.sqlite_event_prefix_review import capture_local_memory_event_prefix
from ark.memory.sqlite_retained_coherent_review import (
    MemoryCoherentHistoryRejected,
    review_retained_coherent_memory,
)


def _setup(tmp_path):
    now = [1000]
    store = SQLiteMemoryStore(
        tmp_path / "timestamp-lifecycle.sqlite", clock_ms=lambda: now[0],
    )
    original = store.put(MemoryWrite(MemoryScope("owner-a", "private"), "a", "first"))
    witnesses = (
        capture_local_memory_event_prefix(store),
        review_memory_event_alignment(store),
    )
    return store, now, original, witnesses


def _append_foreign(store, now):
    now[0] = 4000
    store.put(MemoryWrite(MemoryScope("owner-b", "private"), "b", "second"))


def _rewrite_timestamp(store, record, column, value):
    assert column in {"created_at_ms", "updated_at_ms"}
    with closing(sqlite3.connect(store.path)) as connection:
        with connection:
            changed = connection.execute(
                f"UPDATE memories SET {column}=? WHERE memory_id=?",
                (value, record.memory_id),
            )
            assert changed.rowcount == 1


@pytest.mark.parametrize("column,value", [
    ("created_at_ms", 950),
    ("updated_at_ms", 1050),
])
def test_other_owner_append_does_not_hide_untouched_row_timestamp_rewrite(
    tmp_path, column, value,
):
    store, now, original, witnesses = _setup(tmp_path)
    _append_foreign(store, now)
    _rewrite_timestamp(store, original, column, value)
    with pytest.raises(MemoryCoherentHistoryRejected, match="row/time"):
        review_retained_coherent_memory(store, *witnesses)


@pytest.mark.parametrize("column,value", [
    ("created_at_ms", 900),
    ("updated_at_ms", 2500),
])
def test_other_owner_append_does_not_hide_updated_row_timestamp_rewrite(
    tmp_path, column, value,
):
    store, now, original, witnesses = _setup(tmp_path)
    now[0] = 2000
    store.put(
        MemoryWrite(original.scope, original.source_id, "revised"),
        expected_revision=1,
    )
    _append_foreign(store, now)
    _rewrite_timestamp(store, original, column, value)
    with pytest.raises(MemoryCoherentHistoryRejected, match="row/time"):
        review_retained_coherent_memory(store, *witnesses)


def test_valid_other_owner_append_and_own_update_are_diagnostic_only(tmp_path):
    store, now, original, witnesses = _setup(tmp_path)
    now[0] = 2000
    store.put(
        MemoryWrite(original.scope, original.source_id, "revised"),
        expected_revision=1,
    )
    _append_foreign(store, now)
    review = review_retained_coherent_memory(store, *witnesses)
    assert (review.previous_event_count, review.current_event_count) == (1, 3)
    assert review.status == "ADVANCED_PREFIX_UNAUTHENTICATED"
    assert review.retained_row_delta_checked is False
    assert review.independently_authenticated is False
    assert review.action_authorized is False
    assert review.memory_disclosure_authorized is False


def test_valid_nonmonotonic_synthetic_clock_never_requires_time_order(tmp_path):
    store, now, original, witnesses = _setup(tmp_path)
    now[0] = 100
    store.put(
        MemoryWrite(original.scope, original.source_id, "earlier-clock"),
        expected_revision=1,
    )
    now[0] = 25
    store.put(MemoryWrite(MemoryScope("owner-b", "private"), "b", "foreign"))
    review = review_retained_coherent_memory(store, *witnesses)
    assert review.current_event_count == 3
    assert review.action_authorized is False
