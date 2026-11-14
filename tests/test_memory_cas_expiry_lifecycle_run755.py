"""End-to-end local Memory generation CAS, expiry, and restart isolation.

All rows are synthetic temporary SQLite fixtures. This exercises actual
transactions and event history, not external actions, consent, or provenance.
"""

from __future__ import annotations

import pytest

from ark.memory import MemoryScope, MemoryWrite, SQLiteMemoryStore
from ark.memory.contracts import MemoryConflictError
from ark.memory.generation_fenced_cas import (
    MemoryGenerationCASRejected,
    generation_fenced_memory_update,
    observe_memory_generation_for_cas,
)


def _fixture(tmp_path):
    path = tmp_path / "lifecycle.sqlite3"
    clock = [100]
    store = SQLiteMemoryStore(path, clock_ms=lambda: clock[0])
    private = MemoryScope("owner-a", "private")
    foreign = MemoryScope("owner-b", "private")
    primary = store.put(
        MemoryWrite(private, "shared-source", "first", expires_at_ms=500)
    )
    other = store.put(
        MemoryWrite(foreign, "shared-source", "foreign", expires_at_ms=800)
    )
    token = observe_memory_generation_for_cas(store, private, "shared-source")
    return path, clock, store, private, foreign, primary, other, token


def _operations(store, scope):
    return [(event.operation, event.revision) for event in store.events(scope)]


def test_shortened_retention_survives_restart_then_expires_only_own_scope(tmp_path):
    path, clock, store, private, foreign, primary, other, token = _fixture(tmp_path)
    clock[0] = 200
    changed = generation_fenced_memory_update(
        store,
        MemoryWrite(
            private, "shared-source", "second",
            metadata={"revision": "v2"}, expires_at_ms=350,
        ),
        retained=token,
    )
    assert changed.revision == 2
    assert changed.expires_at_ms == 350
    assert _operations(store, private) == [("create", 1), ("update", 2)]
    assert _operations(store, foreign) == [("create", 1)]

    # A fresh handle must see the committed result, not an in-memory cache.
    cold = SQLiteMemoryStore(path, clock_ms=lambda: 351)
    assert cold.get(primary.memory_id, private) is None
    assert cold.get(primary.memory_id, private, include_expired=True) == changed
    assert cold.get(other.memory_id, foreign) == other
    assert cold.purge_expired(scope=private, limit=1) == 1
    assert cold.get(primary.memory_id, private, include_expired=True) is None
    assert cold.get(other.memory_id, foreign) == other
    assert _operations(cold, private) == [
        ("create", 1), ("update", 2), ("expire", 2),
    ]
    assert _operations(cold, foreign) == [("create", 1)]


@pytest.mark.parametrize("attempted_expiry", [None, 501, 900])
def test_generation_cas_cannot_extend_or_clear_retention(
    tmp_path, attempted_expiry,
):
    path, clock, store, scope, foreign, original, other, token = _fixture(tmp_path)
    clock[0] = 200
    with pytest.raises(MemoryGenerationCASRejected, match="expiry extension"):
        generation_fenced_memory_update(
            store,
            MemoryWrite(
                scope, "shared-source", "must-not-be-written",
                expires_at_ms=attempted_expiry,
            ),
            retained=token,
        )
    cold = SQLiteMemoryStore(path, clock_ms=lambda: 200)
    assert cold.get(original.memory_id, scope, include_expired=True) == original
    assert cold.get(other.memory_id, foreign) == other
    assert _operations(cold, scope) == [("create", 1)]


def test_expired_generation_cannot_be_updated_or_resurrected(tmp_path):
    path, clock, store, scope, foreign, original, other, token = _fixture(tmp_path)
    clock[0] = 500
    with pytest.raises(MemoryConflictError, match="source expired"):
        generation_fenced_memory_update(
            store,
            MemoryWrite(
                scope, "shared-source", "resurrected", expires_at_ms=700,
            ),
            retained=token,
        )
    cold = SQLiteMemoryStore(path, clock_ms=lambda: 500)
    assert cold.get(original.memory_id, scope) is None
    assert cold.get(original.memory_id, scope, include_expired=True) == original
    assert _operations(cold, scope) == [("create", 1)]
    assert cold.get(other.memory_id, foreign) == other


def test_stale_token_remains_denied_after_restart_and_expiry(tmp_path):
    path, clock, store, scope, _, original, _, token = _fixture(tmp_path)
    clock[0] = 200
    generation_fenced_memory_update(
        store,
        MemoryWrite(scope, "shared-source", "updated", expires_at_ms=300),
        retained=token,
    )
    cold = SQLiteMemoryStore(path, clock_ms=lambda: 301)
    assert cold.purge_expired(scope=scope, limit=1) == 1
    before = tuple(cold.events(scope))
    with pytest.raises((MemoryConflictError, MemoryGenerationCASRejected)):
        generation_fenced_memory_update(
            cold,
            MemoryWrite(scope, "shared-source", "stale token attempt"),
            retained=token,
        )
    assert tuple(cold.events(scope)) == before
    assert cold.get(original.memory_id, scope, include_expired=True) is None
