"""Expiry previews cannot mask unrelated missing Memory events.

Disposable SQLite fixtures only; this preview grants no erasure permission.
"""

import sqlite3

import pytest

from ark.memory import MemoryScope, MemoryWrite, SQLiteMemoryStore
from ark.memory.expiry_candidate_preview import (
    MemoryExpiryPreviewRejected,
    review_memory_expiry_candidates,
)


def _fixture(tmp_path):
    store = SQLiteMemoryStore(
        tmp_path / "expiry-highwater.sqlite", clock_ms=lambda: 100,
    )
    due = MemoryScope("owner", "due")
    other = MemoryScope("other", "private")
    store.put(MemoryWrite(due, "due", "synthetic", expires_at_ms=150))
    store.put(MemoryWrite(other, "not-due", "synthetic", expires_at_ms=500))
    store.put(MemoryWrite(other, "not-due-2", "synthetic", expires_at_ms=500))
    return store, due, other


def _review(store, scope):
    return review_memory_expiry_candidates(
        store, scope, now_ms=200, limit=10,
    )


@pytest.mark.parametrize(
    "tamper",
    ("remove_unrelated_middle", "remove_unrelated_tail",
     "advance_sequence", "drop_sequence"),
)
def test_unrelated_event_loss_refuses_otherwise_valid_due_page(tmp_path, tamper):
    store, due, _ = _fixture(tmp_path)
    assert _review(store, due).candidate_count == 1
    with sqlite3.connect(store.path) as conn:
        if tamper == "remove_unrelated_middle":
            conn.execute("DELETE FROM memory_events WHERE event_id=2")
        elif tamper == "remove_unrelated_tail":
            conn.execute("DELETE FROM memory_events WHERE event_id=3")
        elif tamper == "advance_sequence":
            conn.execute(
                "UPDATE sqlite_sequence SET seq=99 WHERE name='memory_events'"
            )
        else:
            conn.execute(
                "DELETE FROM sqlite_sequence WHERE name='memory_events'"
            )
    with pytest.raises(MemoryExpiryPreviewRejected, match="global event high-water"):
        _review(store, due)


def test_no_due_rows_still_refuses_corrupt_foreign_history(tmp_path):
    store, _, other = _fixture(tmp_path)
    # The selected scope has no due rows at this clock, yet the global
    # append history remains part of the local continuity requirement.
    assert _review(store, other).candidate_count == 0
    with sqlite3.connect(store.path) as conn:
        conn.execute("DELETE FROM memory_events WHERE event_id=2")
    with pytest.raises(MemoryExpiryPreviewRejected, match="global event high-water"):
        _review(store, other)


def test_empty_genesis_preview_keeps_non_authorizing_shape(tmp_path):
    store = SQLiteMemoryStore(tmp_path / "empty.sqlite", clock_ms=lambda: 100)
    report = _review(store, MemoryScope("owner", "notes"))
    assert report.candidate_count == 0
    assert report.has_more is False
    assert report.deletion_authorized is False
