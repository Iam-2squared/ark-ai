"""Two independent SQLite handles enforce the SAME generation-token CAS.

These local synthetic races are never evidence of authenticated writer identity,
permission, a trusted clock, retry safety, or a cross-store transaction.
"""

from __future__ import annotations

import pytest

from ark.memory import MemoryScope, MemoryWrite, SQLiteMemoryStore
from ark.memory.ambiguous_commit_pair_review import (
    review_memory_ambiguous_commit_pair,
)
from ark.memory.contracts import MemoryConflictError
from ark.memory.generation_fenced_cas import (
    generation_fenced_memory_update,
    observe_memory_generation_for_cas,
)


@pytest.mark.parametrize("same_payload", (True, False))
def test_two_handles_stale_generation_never_double_apply(tmp_path, same_payload):
    path = tmp_path / "cas-two-writers.sqlite"
    scope = MemoryScope("private-writer", "fixture")
    first = SQLiteMemoryStore(path, clock_ms=lambda: 1000)
    second = SQLiteMemoryStore(path, clock_ms=lambda: 1000)
    initial = first.put(
        MemoryWrite(scope, "source", "original", expires_at_ms=2500)
    )
    retained = observe_memory_generation_for_cas(second, scope, "source")
    winner = MemoryWrite(
        scope, "source", "proposed", {"revision": "one"}, expires_at_ms=2300,
    )
    other = winner if same_payload else MemoryWrite(
        scope, "source", "different", {"revision": "two"}, expires_at_ms=2200,
    )
    generation_fenced_memory_update(first, winner, retained=retained)
    before = first.events(scope)
    row_before = first.get(initial.memory_id, scope, include_expired=True)

    with pytest.raises(MemoryConflictError):
        generation_fenced_memory_update(second, other, retained=retained)

    assert first.events(scope) == before
    assert second.events(scope) == before
    assert row_before.revision == 2
    assert second.get(initial.memory_id, scope, include_expired=True) == row_before

    review = review_memory_ambiguous_commit_pair(second, other, retained=retained)
    expected = "MATCHING_ROW_MANUAL_REVIEW" if same_payload else "DIVERGED_MANUAL_REVIEW"
    assert review.disposition == expected
    assert review.caller_commit_authenticated is False
    assert review.automatic_retry_authorized is False
    assert review.write_authorized is False
    assert review.trusted_clock_verified is False
    assert first.events(scope) == before


def test_old_token_remains_stale_after_new_writer_observes_next_generation(tmp_path):
    path = tmp_path / "cas-second-revision.sqlite"
    scope = MemoryScope("private-writer", "fixture")
    first = SQLiteMemoryStore(path, clock_ms=lambda: 1000)
    second = SQLiteMemoryStore(path, clock_ms=lambda: 1000)
    initial = first.put(MemoryWrite(scope, "source", "v1", expires_at_ms=3000))
    stale = observe_memory_generation_for_cas(first, scope, "source")

    generation_fenced_memory_update(
        second, MemoryWrite(scope, "source", "v2", expires_at_ms=2900),
        retained=stale,
    )
    fresh = observe_memory_generation_for_cas(second, scope, "source")
    generation_fenced_memory_update(
        first, MemoryWrite(scope, "source", "v3", expires_at_ms=2800),
        retained=fresh,
    )
    before = first.events(scope)
    with pytest.raises(MemoryConflictError):
        generation_fenced_memory_update(
            second, MemoryWrite(scope, "source", "v2", expires_at_ms=2700),
            retained=stale,
        )
    assert second.events(scope) == before
    row = first.get(initial.memory_id, scope, include_expired=True)
    assert row.revision == 3
    assert row.content == "v3"
    assert row.expires_at_ms == 2800
