"""Generation-fenced Memory writes reject expiry resurrection and clock rollback."""

from __future__ import annotations

import sqlite3

import pytest

from ark.memory import MemoryScope, MemoryWrite, SQLiteMemoryStore
from ark.memory import generation_fenced_cas as cas
from ark.memory.contracts import MemoryConflictError


def _fixture(tmp_path, *, expires_at_ms=None):
    store = SQLiteMemoryStore(tmp_path / "cas.sqlite", clock_ms=lambda: 1000)
    scope = MemoryScope("offline-test-owner", "private")
    first = store.put(
        MemoryWrite(scope, "stable", "seed", expires_at_ms=expires_at_ms),
        expected_revision=0,
    )
    retained = cas.observe_memory_generation_for_cas(store, scope, "stable")
    return store, scope, first, retained


def _update(store, scope, retained, *, expires_at_ms=None):
    return cas.generation_fenced_memory_update(
        store,
        MemoryWrite(scope, "stable", "updated", expires_at_ms=expires_at_ms),
        retained=retained,
    )


@pytest.mark.parametrize("now,permitted", ((1000, True), (1001, False), (1002, False)))
def test_existing_expiry_is_exclusive_update_boundary(tmp_path, now, permitted):
    store, scope, first, token = _fixture(tmp_path, expires_at_ms=1001)
    store._clock_ms = lambda: now
    if permitted:
        changed = _update(store, scope, token, expires_at_ms=1001)
        assert changed.revision == 2
        assert changed.expires_at_ms == 1001
    else:
        with pytest.raises(MemoryConflictError, match="source expired"):
            _update(store, scope, token, expires_at_ms=1001)
        assert store.get(first.memory_id, scope, include_expired=True).revision == 1
        assert len(store.events(scope)) == 1


@pytest.mark.parametrize("proposed", (0, 999, 1000))
def test_new_expiry_must_be_in_future(tmp_path, proposed):
    store, scope, first, token = _fixture(tmp_path)
    with pytest.raises(cas.MemoryGenerationCASRejected, match="expiry is not future"):
        _update(store, scope, token, expires_at_ms=proposed)
    assert store.get(first.memory_id, scope, include_expired=True).revision == 1
    assert len(store.events(scope)) == 1


def test_future_proposed_expiry_remains_exact(tmp_path):
    store, scope, first, token = _fixture(tmp_path)
    updated = _update(store, scope, token, expires_at_ms=1200)
    assert updated.revision == 2
    assert updated.expires_at_ms == 1200
    assert store.get(first.memory_id, scope, include_expired=True).expires_at_ms == 1200
    assert len(store.events(scope)) == 2


@pytest.mark.parametrize("bad_time", (0, 999))
def test_regressed_update_clock_fails_without_event(tmp_path, bad_time):
    store, scope, first, token = _fixture(tmp_path)
    store._clock_ms = lambda: bad_time
    with pytest.raises(MemoryConflictError, match="clock regressed"):
        _update(store, scope, token)
    assert store.get(first.memory_id, scope, include_expired=True).revision == 1
    assert len(store.events(scope)) == 1


def test_equal_timestamp_compatible_with_existing_v1_history(tmp_path):
    store, scope, _, token = _fixture(tmp_path)
    updated = _update(store, scope, token)
    assert updated.revision == 2
    assert [event.occurred_at_ms for event in store.events(scope)] == [1000, 1000]


def test_backward_persisted_event_clock_rejected_before_token_issuance(tmp_path):
    store, scope, first, _ = _fixture(tmp_path)
    store._clock_ms = lambda: 2000
    store.put(MemoryWrite(scope, "stable", "new"), expected_revision=1)
    with sqlite3.connect(store.path) as conn:
        conn.execute(
            "UPDATE memory_events SET occurred_at_ms=999 "
            "WHERE memory_id=? AND operation='update'",
            (first.memory_id,),
        )
    with pytest.raises(
        cas.MemoryGenerationCASRejected, match="event clock moved backward"
    ):
        cas.observe_memory_generation_for_cas(store, scope, "stable")
    assert len(store.events(scope)) == 2


def test_clock_rejection_occurs_before_event_append(tmp_path, monkeypatch):
    store, scope, _, token = _fixture(tmp_path, expires_at_ms=1001)
    store._clock_ms = lambda: 1001

    def unexpected_event(*args, **kwargs):
        pytest.fail("expired update must not append an event")

    monkeypatch.setattr(store, "_event", unexpected_event)
    with pytest.raises(MemoryConflictError, match="source expired"):
        _update(store, scope, token, expires_at_ms=1001)
