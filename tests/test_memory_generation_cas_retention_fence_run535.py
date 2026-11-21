"""An opt-in Memory generation CAS never silently extends retention."""

from __future__ import annotations

import pytest

from ark.memory import MemoryScope, MemoryWrite, SQLiteMemoryStore
from ark.memory import generation_fenced_cas as cas


@pytest.mark.parametrize("proposed", (None, 1600, 1501))
def test_finite_retention_cannot_be_cleared_or_extended(tmp_path, proposed):
    store = SQLiteMemoryStore(tmp_path / "memory.sqlite", clock_ms=lambda: 1000)
    scope = MemoryScope("synthetic-owner", "private")
    first = store.put(
        MemoryWrite(scope, "stable", "original", expires_at_ms=1500),
        expected_revision=0,
    )
    retained = cas.observe_memory_generation_for_cas(store, scope, "stable")
    before = store.events(scope)

    with pytest.raises(
        cas.MemoryGenerationCASRejected, match="independent authorization"
    ):
        cas.generation_fenced_memory_update(
            store, MemoryWrite(scope, "stable", "bad", expires_at_ms=proposed),
            retained=retained,
        )
    still = store.get(first.memory_id, scope, include_expired=True)
    assert still is not None
    assert still.revision == 1
    assert still.content == "original"
    assert still.expires_at_ms == 1500
    assert store.events(scope) == before


@pytest.mark.parametrize("proposed", (1100, 1400, 1500))
def test_same_or_shorter_finite_expiry_preserves_atomic_cas(tmp_path, proposed):
    store = SQLiteMemoryStore(tmp_path / "memory.sqlite", clock_ms=lambda: 1000)
    scope = MemoryScope("synthetic-owner", "private")
    first = store.put(
        MemoryWrite(scope, "stable", "original", expires_at_ms=1500),
        expected_revision=0,
    )
    retained = cas.observe_memory_generation_for_cas(store, scope, "stable")
    changed = cas.generation_fenced_memory_update(
        store, MemoryWrite(scope, "stable", "new", expires_at_ms=proposed),
        retained=retained,
    )
    assert changed.revision == 2
    assert changed.expires_at_ms == proposed
    assert store.get(first.memory_id, scope, include_expired=True).expires_at_ms == proposed
    assert [event.operation for event in store.events(scope)] == ["create", "update"]


@pytest.mark.parametrize("proposed", (None, 1300))
def test_unbounded_source_can_remain_unbounded_or_be_shortened(tmp_path, proposed):
    store = SQLiteMemoryStore(tmp_path / "memory.sqlite", clock_ms=lambda: 1000)
    scope = MemoryScope("synthetic-owner", "private")
    store.put(MemoryWrite(scope, "stable", "original"), expected_revision=0)
    retained = cas.observe_memory_generation_for_cas(store, scope, "stable")
    updated = cas.generation_fenced_memory_update(
        store, MemoryWrite(scope, "stable", "new", expires_at_ms=proposed),
        retained=retained,
    )
    assert updated.revision == 2
    assert updated.expires_at_ms == proposed
    assert len(store.events(scope)) == 2
