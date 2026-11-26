"""Bounded expiry observations must reconcile the full local event lifecycle.

Synthetic SQLite only; no purge, disclosure, consent or trusted clock implied.
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
    store = SQLiteMemoryStore(tmp_path / "memory.sqlite", clock_ms=lambda: 1000)
    scope = MemoryScope("synthetic-owner", "synthetic")
    first = store.put(
        MemoryWrite(scope, "a", "first local", expires_at_ms=1100),
    )
    second = store.put(
        MemoryWrite(scope, "b", "second local", expires_at_ms=1200),
    )
    return store, scope, first, second


def _preview(store, scope, limit=2):
    return review_memory_expiry_candidates(
        store, scope, now_ms=1300, limit=limit,
    )


@pytest.mark.parametrize(
    "tamper",
    (
        "missing_intermediate",
        "forged_first_revision",
        "early_terminal",
        "forged_event_time",
        "forged_created_time",
        "forged_middle_scope",
    ),
)
def test_expiry_full_chain_rejects_history_that_last_event_alone_misses(
    tmp_path, tamper,
):
    store, scope, first, _ = _fixture(tmp_path)
    updated = store.put(
        MemoryWrite(scope, "a", "first update", expires_at_ms=1100),
        expected_revision=first.revision,
    )
    updated = store.put(
        MemoryWrite(scope, "a", "second update", expires_at_ms=1100),
        expected_revision=updated.revision,
    )
    assert updated.revision == 3
    assert _preview(store, scope).candidate_count == 2

    with sqlite3.connect(store.path) as conn:
        if tamper == "missing_intermediate":
            conn.execute(
                "DELETE FROM memory_events WHERE memory_id=? AND revision=2",
                (first.memory_id,),
            )
        elif tamper == "forged_first_revision":
            conn.execute(
                "UPDATE memory_events SET revision=9 "
                "WHERE memory_id=? AND operation='create'",
                (first.memory_id,),
            )
        elif tamper == "early_terminal":
            conn.execute(
                "UPDATE memory_events SET operation='expire' "
                "WHERE memory_id=? AND revision=2",
                (first.memory_id,),
            )
        elif tamper == "forged_event_time":
            conn.execute(
                "UPDATE memory_events SET occurred_at_ms=1001 "
                "WHERE memory_id=? AND revision=3",
                (first.memory_id,),
            )
        elif tamper == "forged_created_time":
            conn.execute(
                "UPDATE memories SET created_at_ms=999 WHERE memory_id=?",
                (first.memory_id,),
            )
        else:
            conn.execute(
                "UPDATE memory_events SET namespace='foreign' "
                "WHERE memory_id=? AND revision=2",
                (first.memory_id,),
            )
    with pytest.raises(
        MemoryExpiryPreviewRejected, match="matching live Memory event",
    ):
        _preview(store, scope)
    # The diagnostic itself cannot erase a row.
    assert store.get(first.memory_id, scope, include_expired=True) is not None


def test_overflow_row_gets_full_history_validation(tmp_path):
    store, scope, _, second = _fixture(tmp_path)
    changed = store.put(
        MemoryWrite(scope, "b", "second update", expires_at_ms=1200),
        expected_revision=second.revision,
    )
    assert changed.revision == 2
    with sqlite3.connect(store.path) as conn:
        conn.execute(
            "DELETE FROM memory_events WHERE memory_id=? AND revision=1",
            (second.memory_id,),
        )
    with pytest.raises(
        MemoryExpiryPreviewRejected, match="matching live Memory event",
    ):
        _preview(store, scope, limit=1)


def test_delete_and_recreate_same_identity_is_a_valid_new_cycle(tmp_path):
    store, scope, first, _ = _fixture(tmp_path)
    assert store.delete(first.memory_id, scope, expected_revision=1)
    re_created = store.put(
        MemoryWrite(scope, "a", "second lifetime", expires_at_ms=1100),
    )
    assert re_created.memory_id == first.memory_id
    assert re_created.revision == 1
    report = _preview(store, scope)
    assert report.candidate_count == 2
    assert report.has_more is False
    assert verify_memory_expiry_preview(
        report, store, scope, now_ms=1300, limit=2,
        retained_preview_sha256=report.preview_sha256,
    ) is None
    assert report.deletion_authorized is False


def test_normal_update_chain_keeps_preview_bounded(tmp_path):
    store, scope, first, _ = _fixture(tmp_path)
    updated = store.put(
        MemoryWrite(scope, "a", "modified", expires_at_ms=1100),
        expected_revision=first.revision,
    )
    assert updated.revision == 2
    report = _preview(store, scope, limit=1)
    assert report.candidate_count == 1
    assert report.has_more is True
    assert report.physical_erasure_proven is False
