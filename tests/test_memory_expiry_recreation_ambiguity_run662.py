"""Cross-handle expiry ABA must not resurrect old Memory CAS generations.

This uses disposable SQLite, caller-supplied clocks, and no user data.
A matching local row never authenticates a writer or authorizes retry.
"""

from __future__ import annotations

import pytest

from ark.memory import MemoryConflictError, MemoryScope, MemoryWrite, SQLiteMemoryStore
from ark.memory.ambiguous_commit_pair_review import (
    MemoryAmbiguityPairRejected,
    review_memory_ambiguous_commit_pair,
)
from ark.memory.generation_fenced_cas import (
    generation_fenced_memory_update,
    observe_memory_generation_for_cas,
)
from ark.memory.sqlite_event_alignment import review_memory_event_alignment


def _two_handles(tmp_path):
    path = tmp_path / "expiry-aba.sqlite"
    first = SQLiteMemoryStore(path, clock_ms=lambda: 100)
    second = SQLiteMemoryStore(path, clock_ms=lambda: 200)
    scope = MemoryScope("local-fixture-owner", "private")
    created = first.put(
        MemoryWrite(scope, "same-id", "old generation", expires_at_ms=150),
    )
    retained = observe_memory_generation_for_cas(first, scope, "same-id")
    return first, second, scope, created, retained


def test_purged_expiry_then_recreate_cannot_reuse_old_cas_lifetime(tmp_path):
    first, second, scope, created, retained = _two_handles(tmp_path)
    assert second.purge_expired(scope=scope) == 1
    replacement = second.put(
        MemoryWrite(scope, "same-id", "new generation", expires_at_ms=500),
    )
    assert replacement.memory_id == created.memory_id
    assert replacement.revision == created.revision == 1
    before = first.events(scope)
    assert tuple(event.operation for event in before) == (
        "create", "expire", "create",
    )

    stale_proposal = MemoryWrite(
        scope, "same-id", "new generation", expires_at_ms=500,
    )
    with pytest.raises(MemoryConflictError, match="generation changed"):
        generation_fenced_memory_update(
            second, stale_proposal, retained=retained,
        )
    with pytest.raises(MemoryAmbiguityPairRejected):
        review_memory_ambiguous_commit_pair(
            first, stale_proposal, retained=retained,
        )
    assert first.events(scope) == before
    assert first.get(created.memory_id, scope, include_expired=True) == replacement
    assert review_memory_event_alignment(second).event_count == 3


def test_fresh_lifetime_token_still_updates_without_reusing_old_identity(tmp_path):
    first, second, scope, created, old_token = _two_handles(tmp_path)
    assert second.purge_expired(scope=scope) == 1
    second.put(MemoryWrite(scope, "same-id", "new", expires_at_ms=500))
    fresh_token = observe_memory_generation_for_cas(second, scope, "same-id")
    assert old_token.memory_id == fresh_token.memory_id == created.memory_id
    assert fresh_token.create_event_id > old_token.create_event_id
    assert fresh_token.event_prefix_sha256 != old_token.event_prefix_sha256
    changed = generation_fenced_memory_update(
        second, MemoryWrite(scope, "same-id", "revised", expires_at_ms=500),
        retained=fresh_token,
    )
    assert changed.revision == 2
    assert [event.operation for event in first.events(scope)] == [
        "create", "expire", "create", "update",
    ]
    assert review_memory_event_alignment(first).event_count == 4
    with pytest.raises(MemoryConflictError):
        generation_fenced_memory_update(
            second, MemoryWrite(scope, "same-id", "revised", expires_at_ms=500),
            retained=old_token,
        )


@pytest.mark.parametrize("now_ms,allowed", ((149, True), (150, False), (151, False)))
def test_unpurged_expired_generation_cannot_advance_at_deadline(
    tmp_path, now_ms, allowed,
):
    first, _second, scope, created, retained = _two_handles(tmp_path)
    observer = SQLiteMemoryStore(first.path, clock_ms=lambda: now_ms)
    proposed = MemoryWrite(
        scope, "same-id", "updated without extending retention",
        expires_at_ms=150,
    )
    before = first.events(scope)
    if allowed:
        changed = generation_fenced_memory_update(
            observer, proposed, retained=retained,
        )
        assert changed.revision == 2
        assert changed.expires_at_ms == 150
        assert len(first.events(scope)) == len(before) + 1
    else:
        with pytest.raises(MemoryConflictError, match="source expired"):
            generation_fenced_memory_update(
                observer, proposed, retained=retained,
            )
        assert first.events(scope) == before
        assert first.get(created.memory_id, scope, include_expired=True).revision == 1
    assert review_memory_event_alignment(first).row_count == 1
