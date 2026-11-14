"""Read-only Memory ABA diagnosis checks global v1 event custody.

All tests use a disposable local SQLite file. An unbroken event high-water is
only a corruption check, never trusted writer identity, consent or authority.
"""

from __future__ import annotations

import sqlite3

import pytest

from ark.memory import MemoryScope, MemoryWrite, SQLiteMemoryStore
from ark.memory import cas_generation_review as review


def _fixture(tmp_path):
    path = tmp_path / "generation-highwater.sqlite"
    store = SQLiteMemoryStore(path, clock_ms=lambda: 100)
    foreign_scope = MemoryScope("other-owner", "shared")
    target_scope = MemoryScope("target-owner", "private")
    store.put(MemoryWrite(foreign_scope, "one", "foreign-first"))
    target = store.put(MemoryWrite(target_scope, "target", "kept"))
    store.put(MemoryWrite(foreign_scope, "three", "foreign-last"))
    return path, store, target_scope, target


def _review(store, scope, source="target"):
    return review.review_memory_revision_reuse(
        store, scope, source, expected_revision=1,
    )


@pytest.mark.parametrize("removed_id", (1, 2, 3))
def test_missing_global_event_refuses_reused_revision_diagnosis(
    tmp_path, removed_id,
):
    path, store, scope, target = _fixture(tmp_path)
    before = _review(store, scope)
    assert before.generation_count == 1
    assert before.revision_reuse_possible is False
    with sqlite3.connect(path) as conn:
        conn.execute(
            "DELETE FROM memory_events WHERE event_id=?", (removed_id,),
        )
    restarted = SQLiteMemoryStore(path, clock_ms=lambda: 100)
    with pytest.raises(
        review.MemoryGenerationReviewRejected,
        match="global event high-water mismatch",
    ):
        _review(restarted, scope)
    assert restarted.get(target.memory_id, scope).content == "kept"


@pytest.mark.parametrize("new_seq", (0, 4))
def test_modified_global_autoincrement_witness_is_not_trusted(tmp_path, new_seq):
    path, store, scope, target = _fixture(tmp_path)
    with sqlite3.connect(path) as conn:
        conn.execute(
            "UPDATE sqlite_sequence SET seq=? WHERE name='memory_events'",
            (new_seq,),
        )
    with pytest.raises(
        review.MemoryGenerationReviewRejected,
        match="global event high-water mismatch",
    ):
        _review(store, scope)
    assert store.get(target.memory_id, scope).revision == 1


def test_missing_source_cannot_ignore_foreign_global_event_loss(tmp_path):
    path, store, scope, _ = _fixture(tmp_path)
    with sqlite3.connect(path) as conn:
        conn.execute("DELETE FROM memory_events WHERE event_id=1")
    with pytest.raises(
        review.MemoryGenerationReviewRejected,
        match="global event high-water mismatch",
    ):
        _review(store, scope, source="never-created")


def test_unrelated_valid_append_does_not_invent_aba_warning(tmp_path):
    path, _, scope, _ = _fixture(tmp_path)
    store = SQLiteMemoryStore(path, clock_ms=lambda: 200)
    foreign_scope = MemoryScope("other-owner", "shared")
    store.put(MemoryWrite(foreign_scope, "four", "foreign-added"))
    result = _review(store, scope)
    assert result.generation_count == 1
    assert result.event_count == 1
    assert result.live_revision == 1
    assert result.revision_reuse_possible is False
    assert result.write_authorized is False
    assert result.erase_authorized is False
    assert result.generation_authenticated is False
