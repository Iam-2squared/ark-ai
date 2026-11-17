"""Scoped expiry must not hydrate, delete or repair a corrupted foreign row.

Only disposable Memory v1 SQLite fixtures are touched. This checks that the
selected due batch stays confined to the requested owner/namespace; the
result is not authenticated retention policy, consent, or external authority.
"""

from __future__ import annotations

import sqlite3
from contextlib import closing

import pytest

from ark.memory import MemoryScope, MemoryWrite, SQLiteMemoryStore


@pytest.mark.parametrize("column", ("content", "metadata_json", "source_id"))
@pytest.mark.parametrize("other_owner", (False, True))
def test_scoped_due_page_ignores_foreign_storage_class_corruption(
    tmp_path, column: str, other_owner: bool,
) -> None:
    path = tmp_path / "scoped-expiry-foreign-blob.sqlite3"
    local = MemoryScope("synthetic-expiry-owner", "private")
    foreign = (
        MemoryScope("synthetic-foreign-owner", "private")
        if other_owner else MemoryScope("synthetic-expiry-owner", "other-space")
    )
    initial = SQLiteMemoryStore(path, clock_ms=lambda: 100)
    local_due = initial.put(
        MemoryWrite(local, "due", "expire me", expires_at_ms=150)
    )
    local_live = initial.put(
        MemoryWrite(local, "live", "retain me", expires_at_ms=900)
    )
    foreign_due = initial.put(
        MemoryWrite(foreign, "due", "foreign row", expires_at_ms=150)
    )

    with closing(sqlite3.connect(path)) as connection, connection:
        connection.execute(
            f"UPDATE memories SET {column}=CAST(? AS BLOB) WHERE memory_id=?",
            ("corrupted-fixture-only", foreign_due.memory_id),
        )

    cold = SQLiteMemoryStore(path, clock_ms=lambda: 200)
    assert cold.purge_expired(scope=local, limit=1) == 1
    assert cold.get(local_due.memory_id, local, include_expired=True) is None
    assert cold.get(local_live.memory_id, local).content == "retain me"
    assert [(event.event_id, event.operation) for event in cold.events(local)] == [
        (1, "create"), (2, "create"), (4, "expire"),
    ]

    # A cold inspection also must not silently heal or erase the unrelated
    # invalid SQLite storage class, even though the row is now due.
    reopened = SQLiteMemoryStore(path, clock_ms=lambda: 201)
    assert reopened.purge_expired(scope=local, limit=1) == 0
    with closing(sqlite3.connect(path)) as connection:
        assert connection.execute(
            f"SELECT typeof({column}) FROM memories WHERE memory_id=?",
            (foreign_due.memory_id,),
        ).fetchone() == ("blob",)
        assert connection.execute(
            "SELECT event_id,operation FROM memory_events ORDER BY event_id"
        ).fetchall() == [
            (1, "create"), (2, "create"), (3, "create"), (4, "expire"),
        ]
