"""Reject impossible persisted Memory scalars before materializing private rows.

Disposable v1 SQLite fixtures only; no contract/schema changes or live data.
"""

from __future__ import annotations

import sqlite3

import pytest

from ark.memory import (
    MemoryQuery,
    MemorySchemaError,
    MemoryScope,
    MemoryWrite,
    SQLiteMemoryStore,
)


@pytest.mark.parametrize("column", ("created_at_ms", "updated_at_ms", "expires_at_ms"))
@pytest.mark.parametrize("operation", ("get", "search", "put", "delete", "purge"))
def test_negative_persisted_scalar_denied_before_private_row_hydration(
    tmp_path, monkeypatch, column: str, operation: str,
) -> None:
    path = tmp_path / "memory-negative-scalar.sqlite"
    store = SQLiteMemoryStore(path, clock_ms=lambda: 1_000)
    scope = MemoryScope("synthetic-owner", "private")
    initial = store.put(
        MemoryWrite(scope, "synthetic-source", "synthetic private text", expires_at_ms=900)
    )
    with sqlite3.connect(path) as connection:
        connection.execute(
            f"UPDATE memories SET {column}=-1 WHERE memory_id=?",
            (initial.memory_id,),
        )

    sql: list[str] = []
    original_rw = SQLiteMemoryStore._connect
    original_ro = SQLiteMemoryStore._connect_readonly

    def traced_rw(self, *, create=False):
        connection = original_rw(self, create=create)
        connection.set_trace_callback(sql.append)
        return connection

    def traced_ro(self):
        connection = original_ro(self)
        connection.set_trace_callback(sql.append)
        return connection

    monkeypatch.setattr(SQLiteMemoryStore, "_connect", traced_rw)
    monkeypatch.setattr(SQLiteMemoryStore, "_connect_readonly", traced_ro)
    with pytest.raises(MemorySchemaError, match="hydration admission"):
        if operation == "get":
            store.get(initial.memory_id, scope, include_expired=True)
        elif operation == "search":
            store.search(MemoryQuery(scope, include_expired=True))
        elif operation == "put":
            store.put(
                MemoryWrite(scope, "synthetic-source", "updated text", expires_at_ms=900),
                expected_revision=1,
            )
        elif operation == "delete":
            store.delete(initial.memory_id, scope, expected_revision=1)
        else:
            store.purge_expired(scope=scope, limit=1)

    assert not any(
        statement.lstrip().upper().startswith("SELECT * FROM MEMORIES")
        for statement in sql
    ), "persisted scalar corruption must be refused before SELECT * hydration"
    with sqlite3.connect(path) as connection:
        assert connection.execute(
            f"SELECT {column} FROM memories WHERE memory_id=?", (initial.memory_id,),
        ).fetchone() == (-1,)
        assert connection.execute("SELECT COUNT(*) FROM memory_events").fetchone() == (1,)
