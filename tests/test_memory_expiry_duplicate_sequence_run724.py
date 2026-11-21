"""Expiry previews refuse duplicate global SQLite high-water markers.

These checks are read-only on temporary synthetic Memory SQLite fixtures.
A mutable sqlite_sequence is local corruption evidence, never writer identity.
"""

from __future__ import annotations

import sqlite3

import pytest

from ark.memory import MemoryScope, MemoryWrite, SQLiteMemoryStore
from ark.memory.expiry_candidate_preview import (
    MemoryExpiryPreviewRejected,
    review_memory_expiry_candidates,
    verify_memory_expiry_preview,
)


@pytest.mark.parametrize("candidate_mode", ("due", "not_due", "other_scope"))
def test_duplicate_global_event_sequence_refuses_all_expiry_pages(
    tmp_path, candidate_mode,
):
    store = SQLiteMemoryStore(
        tmp_path / "expiry.sqlite", clock_ms=lambda: 1000,
    )
    scope = MemoryScope("owner", "notes")
    foreign = MemoryScope("foreign", "notes")
    store.put(MemoryWrite(scope, "a", "private owner", expires_at_ms=1200))
    store.put(MemoryWrite(foreign, "b", "private foreign", expires_at_ms=1200))
    requested = foreign if candidate_mode == "other_scope" else scope
    now_ms = 1000 if candidate_mode == "not_due" else 1200
    baseline = review_memory_expiry_candidates(
        store, requested, now_ms=now_ms, limit=1,
    )
    assert baseline.candidate_count == (0 if candidate_mode == "not_due" else 1)
    assert baseline.deletion_authorized is False
    with sqlite3.connect(store.path) as conn:
        highwater = conn.execute(
            "SELECT MAX(event_id) FROM memory_events",
        ).fetchone()[0]
        conn.execute(
            "INSERT INTO sqlite_sequence(name,seq) VALUES(?,?)",
            ("memory_events", highwater),
        )
        count = conn.execute(
            "SELECT COUNT(*) FROM sqlite_sequence WHERE name='memory_events'",
        ).fetchone()[0]
        assert count == 2

    with pytest.raises(MemoryExpiryPreviewRejected, match="global event high-water"):
        review_memory_expiry_candidates(store, requested, now_ms=now_ms, limit=1)
    with pytest.raises(MemoryExpiryPreviewRejected, match="global event high-water"):
        verify_memory_expiry_preview(
            baseline, store, requested, now_ms=now_ms, limit=1,
            retained_preview_sha256=baseline.preview_sha256,
        )
    # Neither the failed review nor its retained-receipt check repairs data.
    with sqlite3.connect(store.path) as conn:
        assert conn.execute(
            "SELECT COUNT(*) FROM sqlite_sequence WHERE name='memory_events'",
        ).fetchone()[0] == 2
