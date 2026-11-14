"""Expiry preview observes row and latest event in one read-only SQLite epoch.

These tests use only synthetic Memory v1 data. No actual erasure is authorized.
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


def _fixture(tmp_path):
    path = tmp_path / "memory.sqlite"
    store = SQLiteMemoryStore(path, clock_ms=lambda: 1000)
    scope = MemoryScope("owner", "notes")
    first = store.put(MemoryWrite(scope, "a", "local alpha", expires_at_ms=1200))
    second = store.put(MemoryWrite(scope, "b", "local beta", expires_at_ms=1300))
    return store, scope, first, second


def _preview(store, scope, *, limit=2):
    return review_memory_expiry_candidates(
        store, scope, now_ms=1400, limit=limit,
    )


@pytest.mark.parametrize(
    "tamper",
    ("missing_create", "event_scope", "event_revision", "terminal_event"),
)
def test_expiry_preview_rejects_row_without_live_event(tmp_path, tamper):
    store, scope, first, _ = _fixture(tmp_path)
    assert _preview(store, scope).candidate_count == 2
    with sqlite3.connect(store.path) as conn:
        if tamper == "missing_create":
            conn.execute(
                "DELETE FROM memory_events WHERE memory_id=?", (first.memory_id,),
            )
        elif tamper == "event_scope":
            conn.execute(
                "UPDATE memory_events SET owner_id=? WHERE memory_id=?",
                ("foreign", first.memory_id),
            )
        elif tamper == "event_revision":
            conn.execute(
                "UPDATE memory_events SET revision=? WHERE memory_id=?",
                (7, first.memory_id),
            )
        else:
            conn.execute(
                "UPDATE memory_events SET operation=? WHERE memory_id=?",
                ("delete", first.memory_id),
            )
    with pytest.raises(MemoryExpiryPreviewRejected, match="matching live Memory event"):
        _preview(store, scope)
    assert store.get(first.memory_id, scope, include_expired=True) is not None


def test_extra_pagination_row_is_still_integrity_checked(tmp_path):
    store, scope, _, second = _fixture(tmp_path)
    with sqlite3.connect(store.path) as conn:
        conn.execute(
            "DELETE FROM memory_events WHERE memory_id=?", (second.memory_id,),
        )
    with pytest.raises(MemoryExpiryPreviewRejected, match="matching live Memory event"):
        _preview(store, scope, limit=1)


def test_valid_updated_row_and_event_remain_coherent(tmp_path):
    store, scope, first, _ = _fixture(tmp_path)
    next_row = store.put(
        MemoryWrite(scope, "a", "changed local alpha", expires_at_ms=1399),
        expected_revision=first.revision,
    )
    assert next_row.revision == 2
    result = _preview(store, scope)
    assert result.candidate_count == 2
    assert result.has_more is False
    assert verify_memory_expiry_preview(
        result, store, scope, now_ms=1400, limit=2,
        retained_preview_sha256=result.preview_sha256,
    ) is None
    assert result.deletion_authorized is False
    assert result.trusted_clock_verified is False
