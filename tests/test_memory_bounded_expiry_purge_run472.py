"""Opt-in bounded expiry purge preserves V1 CAS/event transactions."""

from __future__ import annotations

import pytest

from ark.memory import MemoryScope, MemoryWrite, SQLiteMemoryStore


def _fixture(tmp_path, *, count=5):
    store = SQLiteMemoryStore(tmp_path / "memory.sqlite3", clock_ms=lambda: 1000)
    scope = MemoryScope("fixture-person", "private")
    records = [
        store.put(MemoryWrite(scope, f"source-{i}", "synthetic", expires_at_ms=950))
        for i in range(count)
    ]
    return store, scope, records


def test_bounded_batches_advance_in_deterministic_identity_order(tmp_path):
    store, scope, records = _fixture(tmp_path)
    ordered = sorted(record.memory_id for record in records)
    assert store.purge_expired(scope=scope, limit=2) == 2
    expired = [event.memory_id for event in store.events(scope) if event.operation == "expire"]
    assert expired == ordered[:2]
    assert sum(
        store.get(record.memory_id, scope, include_expired=True) is not None
        for record in records
    ) == 3

    assert store.purge_expired(scope=scope, limit=2) == 2
    assert store.purge_expired(scope=scope, limit=2) == 1
    assert store.purge_expired(scope=scope, limit=2) == 0
    final_events = store.events(scope)
    assert [event.memory_id for event in final_events if event.operation == "expire"] == ordered
    assert len(final_events) == 10
    assert all(
        store.get(record.memory_id, scope, include_expired=True) is None
        for record in records
    )


def test_bounded_scope_never_deletes_another_owner(tmp_path):
    store, scope, _ = _fixture(tmp_path)
    foreign = MemoryScope("other-person", "private")
    kept = store.put(MemoryWrite(foreign, "secret", "synthetic", expires_at_ms=900))
    assert store.purge_expired(scope=scope, limit=1) == 1
    assert store.get(kept.memory_id, foreign, include_expired=True) is not None
    assert all(event.operation == "create" for event in store.events(foreign))


def test_global_limit_applies_across_scopes(tmp_path):
    store, scope, records = _fixture(tmp_path, count=3)
    foreign = MemoryScope("other-person")
    extra = store.put(MemoryWrite(foreign, "old", "synthetic", expires_at_ms=900))
    assert store.purge_expired(limit=1) == 1
    remaining = [
        record for record in (*records, extra)
        if store.get(record.memory_id, record.scope, include_expired=True) is not None
    ]
    assert len(remaining) == 3
    assert store.purge_expired(scope=scope, limit=1) <= 1


def test_nonexpired_rows_remain_after_bounded_purge(tmp_path):
    store, scope, _ = _fixture(tmp_path, count=2)
    live = store.put(MemoryWrite(scope, "live", "synthetic", expires_at_ms=1001))
    assert store.purge_expired(scope=scope, limit=1000) == 2
    assert store.get(live.memory_id, scope) is not None
    assert [event.operation for event in store.events(scope)].count("expire") == 2


def test_original_unbounded_default_remains_backward_compatible(tmp_path):
    store, scope, _ = _fixture(tmp_path, count=5)
    assert store.purge_expired(scope=scope) == 5
    assert store.purge_expired(scope=scope) == 0
    assert [event.operation for event in store.events(scope)].count("expire") == 5


@pytest.mark.parametrize("limit", (0, -1, 1001, True, False, 1.0, "2", [], {}))
def test_invalid_batch_limits_rejected_before_any_deletion(tmp_path, limit):
    store, scope, records = _fixture(tmp_path, count=1)
    with pytest.raises(ValueError, match="purge limit"):
        store.purge_expired(scope=scope, limit=limit)
    assert store.get(records[0].memory_id, scope, include_expired=True) is not None
    assert [event.operation for event in store.events(scope)] == ["create"]
