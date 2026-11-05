"""Finite Memory expiry is a local CAS restriction, not a consent receipt.

Disposable SQLite fixtures only. Rejected updates must leave row and journal
unchanged; a delete/recreate must never revive an old generation token.
"""

from __future__ import annotations

import pytest

from ark.memory import MemoryConflictError, MemoryScope, MemoryWrite, SQLiteMemoryStore
from ark.memory.generation_fenced_cas import (
    MemoryGenerationCASRejected,
    generation_fenced_memory_update,
    observe_memory_generation_for_cas,
)
from ark.memory.sqlite_event_alignment import review_memory_event_alignment


@pytest.mark.parametrize("proposed", [None, 201])
def test_generation_cas_cannot_extend_or_clear_finite_expiry(tmp_path, proposed):
    now = {"ms": 100}

    def clock():
        return now["ms"]

    store = SQLiteMemoryStore(tmp_path / "private-expiry.sqlite", clock_ms=clock)
    scope = MemoryScope("local-only-owner", "retained")
    first = store.put(MemoryWrite(scope, "source", "original", expires_at_ms=200))
    retained = observe_memory_generation_for_cas(store, scope, "source")
    baseline = review_memory_event_alignment(store)
    now["ms"] = 150

    with pytest.raises(MemoryGenerationCASRejected, match="expiry extension"):
        generation_fenced_memory_update(
            store,
            MemoryWrite(scope, "source", "not authorized", expires_at_ms=proposed),
            retained=retained,
        )
    assert store.get(first.memory_id, scope, include_expired=True) == first
    assert review_memory_event_alignment(store) == baseline
    assert retained.consent_authenticated is False



def test_same_finite_deadline_is_allowed_without_relaxing_retention(tmp_path):
    store = SQLiteMemoryStore(tmp_path / "same-deadline.sqlite", clock_ms=lambda: 100)
    scope = MemoryScope("local-only-owner", "retained")
    store.put(MemoryWrite(scope, "source", "before", expires_at_ms=200))
    retained = observe_memory_generation_for_cas(store, scope, "source")
    changed = generation_fenced_memory_update(
        store,
        MemoryWrite(scope, "source", "after", expires_at_ms=200),
        retained=retained,
    )
    assert changed.revision == 2
    assert changed.expires_at_ms == 200
    assert changed.content == "after"
    assert review_memory_event_alignment(store).event_count == 2
    assert retained.consent_authenticated is False

def test_shorter_expiry_then_expired_source_and_recreate_never_replay(tmp_path):
    now = {"ms": 100}

    def clock():
        return now["ms"]

    store = SQLiteMemoryStore(tmp_path / "expiry-restart.sqlite", clock_ms=clock)
    scope = MemoryScope("local-only-owner", "private")
    created = store.put(
        MemoryWrite(scope, "source", "before", expires_at_ms=200),
    )
    old_token = observe_memory_generation_for_cas(store, scope, "source")
    now["ms"] = 150
    shortened = generation_fenced_memory_update(
        store,
        MemoryWrite(scope, "source", "retained", expires_at_ms=180),
        retained=old_token,
    )
    assert shortened.revision == 2
    assert shortened.expires_at_ms == 180
    old_evidence = review_memory_event_alignment(store)
    assert old_evidence.event_count == 2
    now["ms"] = 180
    before = observe_memory_generation_for_cas(store, scope, "source")
    with pytest.raises(MemoryConflictError, match="source expired"):
        generation_fenced_memory_update(
            store,
            MemoryWrite(scope, "source", "too late", expires_at_ms=180),
            retained=before,
        )
    assert review_memory_event_alignment(store) == old_evidence

    assert store.purge_expired(scope=scope, limit=1) == 1
    assert store.get(created.memory_id, scope, include_expired=True) is None
    rebuilt = store.put(MemoryWrite(scope, "source", "new lifetime"))
    assert rebuilt.memory_id == created.memory_id
    assert rebuilt.revision == 1
    with pytest.raises(MemoryConflictError, match="generation changed"):
        generation_fenced_memory_update(
            store, MemoryWrite(scope, "source", "stale replay"), retained=old_token,
        )
    final = review_memory_event_alignment(store)
    assert (final.row_count, final.event_count, final.last_event_id) == (1, 4, 4)
    assert store.get(rebuilt.memory_id, scope, include_expired=True) == rebuilt
