"""Memory v1 SQLite CAS, expiry and event integrity across independent handles.

These are local-only concurrency regressions, not external provenance, consent,
secure erasure or user-facing memory authorization.
"""

from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
from threading import Barrier

import pytest

from ark.memory.contracts import (
    MemoryConflictError,
    MemoryScope,
    MemoryWrite,
)
from ark.memory.sqlite_store import SQLiteMemoryStore


def _store(path, now=50):
    return SQLiteMemoryStore(path, clock_ms=lambda: now)


def test_two_independent_store_handles_cannot_both_win_same_revision(tmp_path):
    path = tmp_path / "memory.sqlite"
    scope = MemoryScope("owner-one", "private")
    first = _store(path)
    created = first.put(MemoryWrite(scope, "note", "original"))
    second = _store(path)
    barrier = Barrier(2)

    def contender(store, name):
        barrier.wait(timeout=15)
        try:
            updated = store.put(
                MemoryWrite(scope, "note", name),
                expected_revision=created.revision,
            )
            return ("updated", updated.revision, name)
        except MemoryConflictError:
            return ("conflict", None, name)

    with ThreadPoolExecutor(max_workers=2) as pool:
        left = pool.submit(contender, first, "left")
        right = pool.submit(contender, second, "right")
        results = (left.result(timeout=25), right.result(timeout=25))
    assert sorted(item[0] for item in results) == ["conflict", "updated"]
    assert {item[1] for item in results if item[0] == "updated"} == {2}
    assert first.get(created.memory_id, scope).revision == 2
    assert [item.operation for item in second.events(scope)] == ["create", "update"]
    assert [item.revision for item in second.events(scope)] == [1, 2]


def test_cross_handle_stale_revision_never_appends_a_false_event(tmp_path):
    path = tmp_path / "memory.sqlite"
    scope = MemoryScope("owner-two")
    writer = _store(path)
    reader = _store(path)
    created = writer.put(MemoryWrite(scope, "source", "one"))
    updated = reader.put(
        MemoryWrite(scope, "source", "two"), expected_revision=1,
    )
    assert updated.revision == 2
    with pytest.raises(MemoryConflictError):
        writer.put(MemoryWrite(scope, "source", "stale"), expected_revision=1)
    current = writer.get(created.memory_id, scope)
    assert current is not None
    assert current.content == "two"
    assert current.revision == 2
    assert [(event.operation, event.revision) for event in writer.events(scope)] == [
        ("create", 1), ("update", 2),
    ]


def test_distinct_sources_concurrent_creation_retains_all_event_rows(tmp_path):
    path = tmp_path / "memory.sqlite"
    scope = MemoryScope("owner-three", "shared")
    stores = [_store(path) for _ in range(3)]
    barrier = Barrier(3)

    def create_one(index):
        barrier.wait(timeout=15)
        return stores[index].put(
            MemoryWrite(scope, f"source-{index}", f"content-{index}"),
        )

    with ThreadPoolExecutor(max_workers=3) as pool:
        future = [pool.submit(create_one, index) for index in range(3)]
        records = [item.result(timeout=30) for item in future]
    assert len({item.memory_id for item in records}) == 3
    assert all(item.revision == 1 for item in records)
    events = _store(path).events(scope)
    assert len(events) == 3
    assert {item.memory_id for item in events} == {
        item.memory_id for item in records
    }
    assert all(item.operation == "create" for item in events)


def test_duplicate_delete_from_distinct_handles_is_not_double_logged(tmp_path):
    path = tmp_path / "memory.sqlite"
    scope = MemoryScope("owner-four")
    first = _store(path)
    record = first.put(MemoryWrite(scope, "target", "stored"))
    second = _store(path)
    barrier = Barrier(2)

    def remove(store):
        barrier.wait(timeout=15)
        return store.delete(record.memory_id, scope, expected_revision=1)

    with ThreadPoolExecutor(max_workers=2) as pool:
        a = pool.submit(remove, first)
        b = pool.submit(remove, second)
        results = [a.result(timeout=25), b.result(timeout=25)]
    assert sorted(results) == [False, True]
    assert first.get(record.memory_id, scope) is None
    assert [(event.operation, event.revision) for event in second.events(scope)] == [
        ("create", 1), ("delete", 1),
    ]


def test_expiry_is_inclusive_and_expiration_records_terminal_event(tmp_path):
    path = tmp_path / "memory.sqlite"
    scope = MemoryScope("owner-five")
    writer = _store(path, now=10)
    row = writer.put(MemoryWrite(scope, "timed", "expires", expires_at_ms=20))
    before = _store(path, now=19)
    at_expiry = _store(path, now=20)
    assert before.get(row.memory_id, scope) is not None
    assert at_expiry.get(row.memory_id, scope) is None
    assert at_expiry.get(row.memory_id, scope, include_expired=True) is not None
    assert at_expiry.purge_expired(scope=scope) == 1
    assert at_expiry.purge_expired(scope=scope) == 0
    assert writer.get(row.memory_id, scope, include_expired=True) is None
    assert [(event.operation, event.revision) for event in writer.events(scope)] == [
        ("create", 1), ("expire", 1),
    ]
