"""Synthetic generation review refuses oversized persisted text before hydration.

Only isolated, disposable SQLite files are corrupted; no private user memory,
erase grant, external witness or writable repair path is involved.
"""

from __future__ import annotations

import sqlite3
from contextlib import closing

import pytest

from ark.memory import MemoryScope, MemoryWrite, SQLiteMemoryStore
from ark.memory.cas_generation_review import (
    MemoryGenerationReviewRejected,
    review_memory_revision_reuse,
)


def _created(tmp_path):
    path = tmp_path / "review-text-guard.sqlite"
    scope = MemoryScope("synthetic-owner", "offline")
    store = SQLiteMemoryStore(path, clock_ms=lambda: 1_000)
    record = store.put(MemoryWrite(scope, "source", "bounded"))
    return path, scope, record


@pytest.mark.parametrize("corruption", ("large-content", "large-owner", "blob-meta"))
def test_generation_review_rejects_corrupt_row_before_private_hydration(
    tmp_path, corruption,
):
    path, scope, record = _created(tmp_path)
    with closing(sqlite3.connect(path)) as conn:
        if corruption == "large-content":
            conn.execute(
                "UPDATE memories SET content=? WHERE memory_id=?",
                ("x" * 4_000_001, record.memory_id),
            )
        elif corruption == "large-owner":
            conn.execute(
                "UPDATE memories SET owner_id=? WHERE memory_id=?",
                ("o" * 1_025, record.memory_id),
            )
        else:
            conn.execute(
                "UPDATE memories SET metadata_json=? WHERE memory_id=?",
                (sqlite3.Binary(b"{}"), record.memory_id),
            )
        conn.commit()

    with pytest.raises(
        MemoryGenerationReviewRejected, match="row hydration admission",
    ):
        review_memory_revision_reuse(
            SQLiteMemoryStore(path, clock_ms=lambda: 2_000),
            scope, "source", expected_revision=1,
        )


def test_generation_review_rejects_oversized_event_owner_before_fetchall(tmp_path):
    path, scope, record = _created(tmp_path)
    with closing(sqlite3.connect(path)) as conn:
        conn.execute(
            "UPDATE memory_events SET owner_id=? WHERE memory_id=?",
            ("o" * 1_025, record.memory_id),
        )
        conn.commit()

    with pytest.raises(
        MemoryGenerationReviewRejected, match="event hydration admission",
    ):
        review_memory_revision_reuse(
            SQLiteMemoryStore(path, clock_ms=lambda: 2_000),
            scope, "source", expected_revision=1,
        )


def test_original_memory_generation_remains_reviewable_and_inert(tmp_path):
    path, scope, record = _created(tmp_path)
    review = review_memory_revision_reuse(
        SQLiteMemoryStore(path, clock_ms=lambda: 2_000),
        scope, "source", expected_revision=record.revision,
    )
    assert review.memory_id == record.memory_id
    assert review.event_count == 1
    assert review.generation_count == 1
    assert review.live_revision == 1
    assert review.revision_reuse_possible is False
    assert review.write_authorized is False
    assert review.erase_authorized is False
    assert review.generation_authenticated is False
