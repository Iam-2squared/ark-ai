"""Global event deletion/rewind must block all Memory row+event mutations.

These are local corruption fixtures, not independent audit/provenance evidence.
"""

import sqlite3

import pytest

from ark.memory import MemorySchemaError, MemoryScope, MemoryWrite, SQLiteMemoryStore


@pytest.mark.parametrize("operation", ("put", "delete", "purge"))
@pytest.mark.parametrize("corruption", ("event_gap", "sequence_rewind", "sequence_duplicate"))
def test_mutators_deny_corrupt_global_append_frontier_without_writing(
    tmp_path, operation: str, corruption: str,
) -> None:
    path = tmp_path / "memory.sqlite3"
    scope = MemoryScope("owner-a", "private")
    store = SQLiteMemoryStore(path, clock_ms=lambda: 5_000)
    first = store.put(MemoryWrite(scope, "first", "private one", expires_at_ms=1_000))
    store.put(MemoryWrite(scope, "second", "private two", expires_at_ms=2_000))

    with sqlite3.connect(path) as conn:
        if corruption == "event_gap":
            conn.execute("DELETE FROM memory_events WHERE event_id=1")
        elif corruption == "sequence_rewind":
            conn.execute("UPDATE sqlite_sequence SET seq=1 WHERE name='memory_events'")
        else:
            # sqlite_sequence.name is not unique: a second row must never
            # silently pass a first-row-only history check.
            conn.execute(
                "INSERT INTO sqlite_sequence(name,seq) VALUES('memory_events',2)"
            )
        before_rows = tuple(conn.execute("SELECT * FROM memories ORDER BY memory_id"))
        before_events = tuple(conn.execute("SELECT * FROM memory_events ORDER BY event_id"))
        before_seq = tuple(conn.execute(
            "SELECT name,seq FROM sqlite_sequence ORDER BY rowid"
        ))

    with pytest.raises(MemorySchemaError, match="global memory event append high-water mismatch"):
        if operation == "put":
            store.put(MemoryWrite(scope, "third", "must not persist"))
        elif operation == "delete":
            store.delete(first.memory_id, scope, expected_revision=first.revision)
        else:
            store.purge_expired(scope=scope, limit=1)

    with sqlite3.connect(path) as conn:
        assert tuple(conn.execute("SELECT * FROM memories ORDER BY memory_id")) == before_rows
        assert tuple(conn.execute(
            "SELECT * FROM memory_events ORDER BY event_id"
        )) == before_events
        assert tuple(conn.execute(
            "SELECT name,seq FROM sqlite_sequence ORDER BY rowid"
        )) == before_seq


def test_valid_global_frontier_allows_update_delete_and_expiry(tmp_path) -> None:
    path = tmp_path / "memory.sqlite3"
    scope = MemoryScope("owner-a", "private")
    store = SQLiteMemoryStore(path, clock_ms=lambda: 5_000)
    first = store.put(MemoryWrite(scope, "first", "initial"))
    changed = store.put(
        MemoryWrite(scope, "first", "updated"), expected_revision=first.revision
    )
    assert changed.revision == 2
    assert store.delete(changed.memory_id, scope, expected_revision=2) is True
    store.put(MemoryWrite(scope, "temporary", "expires", expires_at_ms=1_000))
    assert store.purge_expired(scope=scope, limit=1) == 1
    assert [row.operation for row in store.events(scope)] == [
        "create", "update", "delete", "create", "expire",
    ]
