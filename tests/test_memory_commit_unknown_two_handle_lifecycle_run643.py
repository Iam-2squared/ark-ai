"""Read-only COMMIT-UNKNOWN reconciliation across independent SQLite handles.

These tests use disposable local databases and synthetic writers. A matching
row or an unchanged prefix is never caller attribution, retry permission, or
evidence that an external action happened.
"""

from __future__ import annotations

import pytest

from ark.memory import MemoryScope, MemoryWrite, SQLiteMemoryStore
from ark.memory.ambiguous_commit_pair_review import (
    MemoryAmbiguityPairRejected,
    review_memory_ambiguous_commit_pair,
)
from ark.memory.generation_fenced_cas import (
    generation_fenced_memory_update,
    observe_memory_generation_for_cas,
)
from ark.memory.sqlite_event_alignment import review_memory_event_alignment


@pytest.mark.parametrize("owner", ("offline-owner", "日本語の所有者"))
def test_independent_writer_matching_image_is_not_caller_proof(tmp_path, owner):
    path = tmp_path / "independent-commit.sqlite"
    first = SQLiteMemoryStore(path, clock_ms=lambda: 100)
    second = SQLiteMemoryStore(path, clock_ms=lambda: 100)
    scope = MemoryScope(owner, "private")
    created = first.put(MemoryWrite(scope, "source", "before"))
    retained = observe_memory_generation_for_cas(first, scope, "source")
    proposed = MemoryWrite(scope, "source", "after", {"privacy": "local"})

    unchanged = review_memory_ambiguous_commit_pair(
        first, proposed, retained=retained,
    )
    assert unchanged.disposition == "LOCAL_UNCHANGED_REVIEW"
    assert unchanged.automatic_retry_authorized is False

    # Another handle makes a matching change. Its identity is deliberately
    # not available to the diagnostic: identical bytes do not prove authorship.
    generation_fenced_memory_update(second, proposed, retained=retained)
    before_review = second.events(scope)
    before_alignment = review_memory_event_alignment(second)
    result = review_memory_ambiguous_commit_pair(
        first, proposed, retained=retained,
    )
    assert result.disposition == "MATCHING_ROW_MANUAL_REVIEW"
    assert result.caller_commit_authenticated is False
    assert result.automatic_retry_authorized is False
    assert result.write_authorized is False
    assert result.trusted_clock_verified is False
    assert first.get(created.memory_id, scope, include_expired=True).revision == 2
    assert first.events(scope) == before_review
    assert review_memory_event_alignment(second) == before_alignment


@pytest.mark.parametrize("last_content", ("after", "another-value"))
def test_second_independent_update_removes_single_commit_interpretation(
    tmp_path, last_content,
):
    path = tmp_path / "multi-update.sqlite"
    first = SQLiteMemoryStore(path, clock_ms=lambda: 100)
    second = SQLiteMemoryStore(path, clock_ms=lambda: 100)
    scope = MemoryScope("offline-owner", "private")
    first.put(MemoryWrite(scope, "source", "before"))
    retained = observe_memory_generation_for_cas(first, scope, "source")
    proposed = MemoryWrite(scope, "source", "after")
    generation_fenced_memory_update(second, proposed, retained=retained)
    next_token = observe_memory_generation_for_cas(second, scope, "source")
    generation_fenced_memory_update(
        second, MemoryWrite(scope, "source", last_content),
        retained=next_token,
    )
    before = review_memory_event_alignment(first)
    before_events = first.events(scope)
    result = review_memory_ambiguous_commit_pair(
        first, proposed, retained=retained,
    )
    assert result.disposition == "DIVERGED_MANUAL_REVIEW"
    assert result.automatic_retry_authorized is False
    assert result.caller_commit_authenticated is False
    assert before.event_count == 3
    assert first.events(scope) == before_events
    assert review_memory_event_alignment(second) == before


def test_old_generation_after_delete_and_recreate_requires_manual_triage(tmp_path):
    path = tmp_path / "recreated.sqlite"
    first = SQLiteMemoryStore(path, clock_ms=lambda: 100)
    second = SQLiteMemoryStore(path, clock_ms=lambda: 100)
    scope = MemoryScope("offline-owner", "private")
    saved = first.put(MemoryWrite(scope, "source", "before"))
    retained = observe_memory_generation_for_cas(first, scope, "source")
    assert second.delete(saved.memory_id, scope, expected_revision=1)
    second.put(MemoryWrite(scope, "source", "recreated"), expected_revision=0)
    before = review_memory_event_alignment(first)
    with pytest.raises(MemoryAmbiguityPairRejected):
        review_memory_ambiguous_commit_pair(
            first, MemoryWrite(scope, "source", "after"), retained=retained,
        )
    assert review_memory_event_alignment(first) == before
