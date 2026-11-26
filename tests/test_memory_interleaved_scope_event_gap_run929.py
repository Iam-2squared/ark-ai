"""Interleaved Memory event IDs remain scoped and globally gap-fenced.

Disposable SQLite fixtures only; no consent, independent witness or external
effect is authenticated by this test.
"""

from __future__ import annotations

import sqlite3

import pytest

from ark.memory import (
    MemoryConflictError,
    MemorySchemaError,
    MemoryScope,
    MemoryWrite,
    SQLiteMemoryStore,
)


@pytest.mark.parametrize(
    ("other_owner", "other_namespace"),
    (("foreign-owner", "private"), ("primary-owner", "foreign-space")),
)
def test_interleaved_scope_events_page_by_global_id_across_reopen(
    tmp_path, other_owner: str, other_namespace: str,
) -> None:
    path = tmp_path / "interleaved-memory.sqlite"
    primary = MemoryScope("primary-owner", "private")
    foreign = MemoryScope(other_owner, other_namespace)
    first = SQLiteMemoryStore(path, clock_ms=lambda: 1_000)
    second = SQLiteMemoryStore(path, clock_ms=lambda: 1_001)

    a = first.put(MemoryWrite(primary, "common-source", "first"))
    b = second.put(MemoryWrite(foreign, "common-source", "second"))
    a2 = first.put(
        MemoryWrite(primary, "common-source", "first-updated"),
        expected_revision=1,
    )
    b2 = second.put(
        MemoryWrite(foreign, "common-source", "second-updated"),
        expected_revision=1,
    )
    assert a.memory_id == a2.memory_id
    assert b.memory_id == b2.memory_id
    assert a.memory_id != b.memory_id
    assert first.delete(a.memory_id, primary, expected_revision=2) is True

    with pytest.raises(MemoryConflictError):
        second.put(
            MemoryWrite(foreign, "common-source", "stale-foreign"),
            expected_revision=1,
        )
    with pytest.raises(MemoryConflictError):
        second.delete(b.memory_id, foreign, expected_revision=1)

    reopened = SQLiteMemoryStore(path, clock_ms=lambda: 1_002)
    assert reopened.get(a.memory_id, primary) is None
    assert reopened.get(b.memory_id, foreign).content == "second-updated"
    assert reopened.get(b.memory_id, foreign).revision == 2

    a_events = reopened.events(primary)
    b_events = reopened.events(foreign)
    assert [(event.event_id, event.operation, event.revision) for event in a_events] == [
        (1, "create", 1), (3, "update", 2), (5, "delete", 2),
    ]
    assert [(event.event_id, event.operation, event.revision) for event in b_events] == [
        (2, "create", 1), (4, "update", 2),
    ]
    assert [event.event_id for event in reopened.events(
        primary, after_event_id=1, limit=1,
    )] == [3]
    assert [event.event_id for event in reopened.events(
        foreign, after_event_id=2, limit=1,
    )] == [4]
    assert reopened.events(primary, after_event_id=5) == []
    assert reopened.events(foreign, after_event_id=4) == []


@pytest.mark.parametrize("removed_foreign_id", (2, 4))
def test_foreign_scope_event_gap_denies_other_scope_history(
    tmp_path, removed_foreign_id: int,
) -> None:
    path = tmp_path / "cross-scope-gap.sqlite"
    primary = MemoryScope("primary-owner", "private")
    foreign = MemoryScope("foreign-owner", "private")
    store = SQLiteMemoryStore(path, clock_ms=lambda: 1_000)
    a = store.put(MemoryWrite(primary, "a", "alpha"))
    b = store.put(MemoryWrite(foreign, "b", "beta"))
    store.put(MemoryWrite(primary, "a", "alpha-2"), expected_revision=1)
    store.put(MemoryWrite(foreign, "b", "beta-2"), expected_revision=1)
    assert a.memory_id != b.memory_id
    assert [event.event_id for event in store.events(primary)] == [1, 3]
    assert [event.event_id for event in store.events(foreign)] == [2, 4]

    # Simulate a malicious history gap in a disposable DB only. A scoped
    # read must not overlook foreign-owner evidence loss.
    with sqlite3.connect(path) as conn:
        conn.execute(
            "DELETE FROM memory_events WHERE event_id=?", (removed_foreign_id,),
        )
    reopened = SQLiteMemoryStore(path, clock_ms=lambda: 1_001)
    with pytest.raises(MemorySchemaError, match="high-water mismatch"):
        reopened.events(primary)
