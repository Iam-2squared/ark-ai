"""Memory writers must acquire SQLite writer ownership before clock and CAS reads."""

import sqlite3
from contextlib import closing

import pytest

from ark.memory import MemoryConflictError, MemoryScope, MemoryWrite, SQLiteMemoryStore


@pytest.mark.parametrize("operation", ["create", "update", "delete"])
def test_clock_observes_write_lock_for_mutation(tmp_path, operation: str) -> None:
    path = tmp_path / "memory.sqlite3"
    checking = {"enabled": False, "count": 0}

    def clock() -> int:
        if checking["enabled"]:
            checking["count"] += 1
            with closing(sqlite3.connect(path, timeout=0.01)) as competing:
                with pytest.raises(sqlite3.OperationalError, match="locked"):
                    competing.execute("BEGIN IMMEDIATE")
        return 1000

    store = SQLiteMemoryStore(path, clock_ms=clock)
    scope = MemoryScope("synthetic-owner", "synthetic-namespace")
    first = None
    if operation != "create":
        first = store.put(MemoryWrite(scope, "synthetic-source", "version-1"))
    checking["enabled"] = True
    if operation == "create":
        record = store.put(MemoryWrite(scope, "synthetic-source", "version-1"))
        assert record.revision == 1
    elif operation == "update":
        assert first is not None
        record = store.put(
            MemoryWrite(scope, "synthetic-source", "version-2"),
            expected_revision=first.revision,
        )
        assert record.revision == 2
    else:
        assert first is not None
        assert store.delete(first.memory_id, scope, expected_revision=first.revision)
    checking["enabled"] = False
    assert checking["count"] == 1


def test_stale_writers_report_typed_conflict_and_leave_audit_intact(tmp_path) -> None:
    path = tmp_path / "memory.sqlite3"
    left = SQLiteMemoryStore(path, clock_ms=lambda: 1000)
    right = SQLiteMemoryStore(path, clock_ms=lambda: 2000)
    scope = MemoryScope("synthetic-owner", "synthetic-namespace")
    first = left.put(MemoryWrite(scope, "synthetic-source", "v1"))
    second = right.put(
        MemoryWrite(scope, "synthetic-source", "v2"), expected_revision=first.revision
    )
    with pytest.raises(MemoryConflictError):
        left.put(MemoryWrite(scope, "synthetic-source", "stale"), expected_revision=1)
    with pytest.raises(MemoryConflictError):
        left.put(MemoryWrite(scope, "synthetic-source", "duplicate-create"))
    with pytest.raises(MemoryConflictError):
        left.delete(first.memory_id, scope, expected_revision=1)
    assert left.get(second.memory_id, scope, include_expired=True) == second
    assert [(event.operation, event.revision) for event in left.events(scope)] == [
        ("create", 1),
        ("update", 2),
    ]
