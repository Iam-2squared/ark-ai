"""Single SQLite read snapshot for Memory v1 rows and event continuity."""

from __future__ import annotations

import sqlite3

import pytest

import ark.memory.atomic_epoch_review as mod
from ark.memory.contracts import MemorySchemaError, MemoryScope, MemoryWrite
from ark.memory.sqlite_store import SQLiteMemoryStore


def _store(tmp_path, now=1000):
    return SQLiteMemoryStore(
        tmp_path / "memory-epoch.sqlite", clock_ms=lambda: now,
    )


def _write(store, namespace, source):
    return store.put(MemoryWrite(
        MemoryScope("owner", namespace), source,
        "private body: never return this",
        metadata={"private": "do not expose"},
    ))


def test_empty_epoch_is_bounded_and_non_authorizing(tmp_path):
    store = _store(tmp_path)
    scopes = (MemoryScope("owner", "a"), MemoryScope("owner", "b"))
    result = mod.review_atomic_memory_epoch(store, scopes)
    assert result == mod.review_atomic_memory_epoch(store, scopes)
    assert result.row_counts == (0, 0)
    assert result.event_counts == (0, 0)
    assert result.event_tail_ids == (0, 0)
    assert len(result.scope_fingerprints) == 2
    assert len(result.epoch_digest) == 64
    assert "owner" not in repr(result)
    assert result.independent_writer_proven is False
    assert result.cross_store_atomicity_proven is False
    assert result.trusted_clock_proven is False
    assert result.memory_disclosure_authorized is False
    assert result.dispatch_authorized is False


def test_create_update_and_delete_change_event_epoch_without_content(tmp_path):
    store = _store(tmp_path)
    a = MemoryScope("owner", "a")
    _write(store, "a", "first")
    first = mod.review_atomic_memory_epoch(store, (a,))
    assert first.row_counts == (1,)
    assert first.event_counts == (1,)
    record = store.put(MemoryWrite(a, "first", "new private text"), expected_revision=1)
    second = mod.review_atomic_memory_epoch(store, (a,))
    assert second.row_counts == (1,)
    assert second.event_counts == (2,)
    assert second.event_tail_ids[0] > first.event_tail_ids[0]
    assert second.epoch_digest != first.epoch_digest
    assert store.delete(record.memory_id, a, expected_revision=2)
    third = mod.review_atomic_memory_epoch(store, (a,))
    assert third.row_counts == (0,)
    assert third.event_counts == (3,)
    assert third.epoch_digest != second.epoch_digest
    for witness in (first, second, third):
        assert "private" not in repr(witness)
        assert "new private text" not in repr(witness)


def test_namespace_isolation_and_deterministic_order(tmp_path):
    store = _store(tmp_path)
    _write(store, "a", "first")
    _write(store, "b", "second")
    scopes = (MemoryScope("owner", "a"), MemoryScope("owner", "b"))
    one = mod.review_atomic_memory_epoch(store, scopes)
    assert one.row_counts == (1, 1)
    assert one.event_counts == (1, 1)
    assert one.event_tail_ids[1] > one.event_tail_ids[0]
    assert one == mod.review_atomic_memory_epoch(store, scopes)
    with pytest.raises(MemorySchemaError, match="ordered"):
        mod.review_atomic_memory_epoch(store, tuple(reversed(scopes)))


def test_clock_callback_writer_does_not_mix_row_and_event_epochs(tmp_path):
    store = _store(tmp_path)
    peer = SQLiteMemoryStore(store.path, clock_ms=lambda: 1001)
    _write(store, "a", "before")
    scope = MemoryScope("owner", "a")
    calls = []

    def concurrent_clock():
        calls.append(True)
        _write(peer, "a", "during")
        return 1000

    store._clock_ms = concurrent_clock
    sealed = mod.review_atomic_memory_epoch(store, (scope,))
    assert len(calls) == 1
    assert sealed.row_counts == (1,)
    assert sealed.event_counts == (1,)
    store._clock_ms = lambda: 1002
    after = mod.review_atomic_memory_epoch(store, (scope,))
    assert after.row_counts == (2,)
    assert after.event_counts == (2,)


@pytest.mark.parametrize("scopes", [
    (), (MemoryScope("owner", "a"), MemoryScope("owner", "a")),
    (MemoryScope("owner", "a"), MemoryScope("other", "b")),
    (MemoryScope("owner", "b"), MemoryScope("owner", "a")),
    ("owner",), [MemoryScope("owner", "a")],
])
def test_malformed_or_cross_owner_scopes_rejected(tmp_path, scopes):
    store = _store(tmp_path)
    with pytest.raises(MemorySchemaError):
        mod.review_atomic_memory_epoch(store, scopes)


def test_deleted_file_not_recreated_on_review(tmp_path):
    store = _store(tmp_path)
    store.path.unlink()
    with pytest.raises(MemorySchemaError, match="read-only"):
        mod.review_atomic_memory_epoch(store, (MemoryScope("owner", "a"),))
    assert not store.path.exists()


def test_bad_event_row_rejected_before_return(tmp_path):
    store = _store(tmp_path)
    _write(store, "a", "first")
    with sqlite3.connect(store.path) as conn:
        conn.execute("UPDATE memory_events SET occurred_at_ms=-1 WHERE event_id=1")
    with pytest.raises(MemorySchemaError, match="invalid persisted event"):
        mod.review_atomic_memory_epoch(store, (MemoryScope("owner", "a"),))


def test_scope_retarged_in_clock_callback_is_denied(tmp_path):
    store = _store(tmp_path)
    scope = MemoryScope("owner", "a")

    def drift():
        object.__setattr__(scope, "namespace", "b")
        return 1000

    store._clock_ms = drift
    with pytest.raises(MemorySchemaError, match="changed"):
        mod.review_atomic_memory_epoch(store, (scope,))


@pytest.mark.parametrize("name", (
    "independent_writer_proven", "cross_store_atomicity_proven",
    "trusted_clock_proven", "memory_disclosure_authorized",
    "dispatch_authorized",
))
def test_forged_result_authority_fails(monkeypatch, tmp_path, name):
    store = _store(tmp_path)
    monkeypatch.setattr(
        mod.AtomicMemoryEpochReview, name, property(lambda _: True),
    )
    with pytest.raises(MemorySchemaError, match="result changed"):
        mod.review_atomic_memory_epoch(store, (MemoryScope("owner", "a"),))
