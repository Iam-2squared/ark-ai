"""Durable Memory expiry and CAS witnesses across independent SQLite handles.

All data and clocks are synthetic. Event continuity does not authenticate
independent writer identity or prove deletion from any external backup.
"""

from __future__ import annotations

import pytest

from ark.memory import (
    MemoryConflictError,
    MemoryQuery,
    MemoryScope,
    MemoryWrite,
    SQLiteMemoryStore,
)


def test_expired_delete_blocks_stale_writer_without_touching_other_namespace(
    tmp_path,
):
    path = tmp_path / "memory.sqlite"
    private = MemoryScope("fixture-owner", "private")
    public = MemoryScope("fixture-owner", "public")
    original = SQLiteMemoryStore(path, clock_ms=lambda: 100)
    stale = original.put(MemoryWrite(private, "same-source", "old", expires_at_ms=150))
    other = original.put(MemoryWrite(public, "other-source", "retain"))
    reopened = SQLiteMemoryStore(path, clock_ms=lambda: 200)
    assert reopened.get(stale.memory_id, private) is None
    assert reopened.get(stale.memory_id, private, include_expired=True) is not None
    assert reopened.purge_expired(scope=private) == 1
    assert reopened.get(stale.memory_id, private, include_expired=True) is None
    assert reopened.get(other.memory_id, public).content == "retain"
    with pytest.raises(MemoryConflictError):
        original.put(
            MemoryWrite(private, "same-source", "stale replacement"),
            expected_revision=stale.revision,
        )
    assert original.search(MemoryQuery(private, include_expired=True)) == []
    events = reopened.events(private)
    assert [event.operation for event in events] == ["create", "expire"]
    assert [event.revision for event in events] == [1, 1]
    assert [event.operation for event in reopened.events(public)] == ["create"]
    assert [event.event_id for event in events] == [1, 3]
    assert original.get(other.memory_id, public).revision == 1


def test_bounded_purge_restarts_without_duplicate_expiry_events(tmp_path):
    path = tmp_path / "memory.sqlite"
    scope = MemoryScope("fixture-owner", "expiring")
    writer = SQLiteMemoryStore(path, clock_ms=lambda: 100)
    records = [
        writer.put(MemoryWrite(scope, "source-" + str(i), "fixture", expires_at_ms=150))
        for i in range(3)
    ]
    other = SQLiteMemoryStore(path, clock_ms=lambda: 200)
    assert other.purge_expired(scope=scope, limit=1) == 1
    first_pass = other.events(scope)
    assert [event.operation for event in first_pass].count("expire") == 1
    restarted = SQLiteMemoryStore(path, clock_ms=lambda: 200)
    assert restarted.purge_expired(scope=scope, limit=1) == 1
    assert restarted.purge_expired(scope=scope, limit=1) == 1
    assert restarted.purge_expired(scope=scope, limit=1) == 0
    assert restarted.purge_expired(scope=scope) == 0
    assert all(
        restarted.get(record.memory_id, scope, include_expired=True) is None
        for record in records
    )
    events = restarted.events(scope)
    assert len(events) == 6
    assert [event.event_id for event in events] == list(range(1, 7))
    assert [event.operation for event in events].count("create") == 3
    assert [event.operation for event in events].count("expire") == 3
