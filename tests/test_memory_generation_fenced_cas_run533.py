"""Opt-in SQLite writer fences a Memory lifetime and its event prefix atomically."""

from __future__ import annotations

import hashlib
import sqlite3
from concurrent.futures import ThreadPoolExecutor
from threading import Barrier

import pytest

from ark.memory import MemoryScope, MemoryWrite, SQLiteMemoryStore
from ark.memory import generation_fenced_cas as cas
from ark.memory.contracts import MemoryConflictError


def _fixture(tmp_path):
    path = tmp_path / "generation.sqlite"
    store = SQLiteMemoryStore(path, clock_ms=lambda: 1000)
    scope = MemoryScope("synthetic-owner", "private")
    first = store.put(MemoryWrite(scope, "fixed-source", "first"), expected_revision=0)
    token = cas.observe_memory_generation_for_cas(store, scope, "fixed-source")
    return path, store, scope, first, token


def _update(store, scope, token, content="updated"):
    return cas.generation_fenced_memory_update(
        store, MemoryWrite(scope, "fixed-source", content), retained=token,
    )


def test_atomic_update_advances_existing_row_and_event_together(tmp_path):
    _, store, scope, first, token = _fixture(tmp_path)
    assert token.revision == 1
    assert token.create_event_id == token.last_event_id
    assert token.external_action_authorized is False
    assert token.consent_authenticated is False

    next_record = _update(store, scope, token)
    assert next_record.memory_id == first.memory_id
    assert next_record.revision == 2
    assert next_record.content == "updated"
    assert store.get(first.memory_id, scope).content == "updated"
    events = store.events(scope)
    assert [(e.operation, e.revision) for e in events] == [
        ("create", 1), ("update", 2),
    ]
    fresh = cas.observe_memory_generation_for_cas(store, scope, "fixed-source")
    assert fresh.create_event_id == token.create_event_id
    assert fresh.last_event_id > token.last_event_id
    assert fresh.event_prefix_sha256 != token.event_prefix_sha256


def test_retained_token_is_one_shot_against_same_generation_update(tmp_path):
    _, store, scope, _, token = _fixture(tmp_path)
    _update(store, scope, token)
    before = store.events(scope)
    with pytest.raises(MemoryConflictError, match="generation changed"):
        _update(store, scope, token, content="wrong")
    assert store.events(scope) == before


def test_delete_recreate_same_id_and_revision_rejects_aba_write(tmp_path):
    path, store, scope, first, old_token = _fixture(tmp_path)
    store.delete(first.memory_id, scope, expected_revision=1)
    restarted = SQLiteMemoryStore(path, clock_ms=lambda: 2000)
    new = restarted.put(
        MemoryWrite(scope, "fixed-source", "new generation"),
        expected_revision=0,
    )
    assert new.memory_id == first.memory_id
    assert new.revision == old_token.revision == 1
    with pytest.raises(MemoryConflictError, match="generation changed"):
        _update(store, scope, old_token, content="stale writer")
    assert restarted.get(first.memory_id, scope).content == "new generation"
    fresh = cas.observe_memory_generation_for_cas(restarted, scope, "fixed-source")
    assert fresh.create_event_id != old_token.create_event_id
    assert _update(restarted, scope, fresh, content="valid new writer").revision == 2


def test_cross_handle_restart_fresh_token_works(tmp_path):
    path, _, scope, first, old_token = _fixture(tmp_path)
    reopened = SQLiteMemoryStore(path, clock_ms=lambda: 3000)
    item = _update(reopened, scope, old_token)
    assert item.revision == 2
    assert reopened.get(first.memory_id, scope).content == "updated"


def test_two_competing_writers_cannot_both_consume_one_token(tmp_path):
    path, store, scope, _, token = _fixture(tmp_path)
    other = SQLiteMemoryStore(path, clock_ms=lambda: 2000)
    barrier = Barrier(2)

    def commit(selected, value):
        barrier.wait(timeout=10)
        try:
            return _update(selected, scope, token, value)
        except MemoryConflictError:
            return None

    with ThreadPoolExecutor(max_workers=2) as pool:
        pending = (
            pool.submit(commit, store, "winner a"),
            pool.submit(commit, other, "winner b"),
        )
        observed = [task.result(timeout=25) for task in pending]
    assert sum(record is not None for record in observed) == 1
    events = store.events(scope)
    assert [event.operation for event in events] == ["create", "update"]


@pytest.mark.parametrize("field,value", (
    ("create_event_id", True),
    ("create_event_id", -1),
    ("last_event_id", 0),
    ("revision", 1.0),
    ("event_prefix_sha256", "wrong"),
    ("row_sha256", "0" * 64),
    ("memory_id", "mem_" + "f" * 64),
))
def test_modified_or_forged_token_cannot_mutate_memory(tmp_path, field, value):
    _, store, scope, first, token = _fixture(tmp_path)
    object.__setattr__(token, field, value)
    with pytest.raises((cas.MemoryGenerationCASRejected, MemoryConflictError)):
        _update(store, scope, token)
    assert store.get(first.memory_id, scope).revision == 1
    assert len(store.events(scope)) == 1


def test_row_tamper_with_recomputed_content_hash_still_conflicts(tmp_path):
    path, store, scope, first, token = _fixture(tmp_path)
    tampered = "secretly changed without update event"
    with sqlite3.connect(path) as conn:
        conn.execute(
            "UPDATE memories SET content=?,content_sha256=? WHERE memory_id=?",
            (tampered, hashlib.sha256(tampered.encode()).hexdigest(), first.memory_id),
        )
    with pytest.raises(MemoryConflictError, match="generation changed"):
        _update(store, scope, token)
    assert len(store.events(scope)) == 1


def test_event_history_identity_tamper_is_rejected(tmp_path):
    path, store, scope, first, token = _fixture(tmp_path)
    with sqlite3.connect(path) as conn:
        conn.execute(
            "UPDATE memory_events SET namespace='other' WHERE memory_id=?",
            (first.memory_id,),
        )
    with pytest.raises(cas.MemoryGenerationCASRejected, match="identity"):
        _update(store, scope, token)
    assert store.get(first.memory_id, scope).revision == 1


def test_invalid_clock_rolls_back_row_and_event(tmp_path):
    _, store, scope, first, token = _fixture(tmp_path)
    store._clock_ms = lambda: True
    with pytest.raises(ValueError, match="clock"):
        _update(store, scope, token)
    assert store.get(first.memory_id, scope, include_expired=True).revision == 1
    assert len(store.events(scope)) == 1


def test_clock_callback_cannot_retarget_caller_write_before_commit(tmp_path):
    _, store, scope, first, token = _fixture(tmp_path)
    write = MemoryWrite(scope, "fixed-source", "intended")

    def retarget():
        object.__setattr__(write, "content", "changed")
        return 2000

    store._clock_ms = retarget
    with pytest.raises(cas.MemoryGenerationCASRejected, match="inputs changed"):
        cas.generation_fenced_memory_update(store, write, retained=token)
    assert store.get(first.memory_id, scope, include_expired=True).revision == 1
    assert len(store.events(scope)) == 1


def test_missing_row_is_not_implicitly_created(tmp_path):
    _, store, scope, first, token = _fixture(tmp_path)
    store.delete(first.memory_id, scope, expected_revision=1)
    before = store.events(scope)
    with pytest.raises(MemoryConflictError, match="existing row"):
        _update(store, scope, token)
    assert store.events(scope) == before


def test_bounded_event_history_cannot_be_partially_verified(tmp_path, monkeypatch):
    _, store, scope, first, token = _fixture(tmp_path)
    monkeypatch.setattr(cas, "_MAX_EVENTS", 0)
    with pytest.raises(cas.MemoryGenerationCASRejected, match="unbounded"):
        _update(store, scope, token)
    assert store.get(first.memory_id, scope).revision == 1
