"""Scope-specific SQLite prehydration rejects poison without cross-scope leakage.

Only new disposable fixture databases are modified. A healthy owner can still
read/purge its own scope when an unrelated row has malformed SQLite storage.
This is neither private user-data access nor authenticated writer evidence.
"""

from __future__ import annotations

import sqlite3
from contextlib import closing

import pytest

from ark.memory import MemorySchemaError, MemoryScope, MemoryWrite, SQLiteMemoryStore
from ark.memory.contracts import MemoryQuery


@pytest.mark.parametrize("column", ("content", "metadata_json", "source_id"))
@pytest.mark.parametrize("operation", ("get", "search"))
def test_foreign_blob_rejected_only_if_selected(
    tmp_path, column: str, operation: str,
) -> None:
    path = tmp_path / "isolated-scopes.sqlite3"
    local_scope = MemoryScope("fixture-local", "private")
    foreign_scope = MemoryScope("fixture-foreign", "private")
    store = SQLiteMemoryStore(path, clock_ms=lambda: 100)
    local = store.put(MemoryWrite(local_scope, "local-source", "local-text"))
    foreign = store.put(MemoryWrite(foreign_scope, "foreign-source", "foreign-text"))

    # SQLite's TEXT affinity permits persisted BLOBs in a corrupt fixture.
    # Neither a local GET nor local SEARCH should hydrate a foreign row.
    with closing(sqlite3.connect(path)) as conn, conn:
        conn.execute(
            f"UPDATE memories SET {column}=CAST(? AS BLOB) WHERE memory_id=?",
            ("synthetic-corruption", foreign.memory_id),
        )

    cold = SQLiteMemoryStore(path, clock_ms=lambda: 101)
    if operation == "get":
        healthy = cold.get(local.memory_id, local_scope, include_expired=True)
        assert healthy is not None
        assert healthy.content == "local-text"
    else:
        healthy = cold.search(MemoryQuery(local_scope, include_expired=True))
        assert [entry.memory_id for entry in healthy] == [local.memory_id]

    # The same corrupt row is refused when actually selected. There is no
    # opportunistic repair, migration, re-attribution or event append.
    with pytest.raises(MemorySchemaError, match="stored memory row exceeds"):
        if operation == "get":
            cold.get(foreign.memory_id, foreign_scope, include_expired=True)
        else:
            cold.search(MemoryQuery(foreign_scope, include_expired=True))

    with closing(sqlite3.connect(path)) as conn:
        assert conn.execute(
            f"SELECT typeof({column}) FROM memories WHERE memory_id=?",
            (foreign.memory_id,),
        ).fetchone() == ("blob",)
        assert conn.execute(
            "SELECT COUNT(*) FROM memory_events"
        ).fetchone() == (2,)
    assert [event.operation for event in cold.events(local_scope)] == ["create"]


@pytest.mark.parametrize("column", ("content", "metadata_json", "source_id"))
def test_scoped_expiry_does_not_hydrate_corrupt_foreign_due_row(
    tmp_path, column: str,
) -> None:
    path = tmp_path / "scoped-expiry.sqlite3"
    local_scope = MemoryScope("fixture-local", "private")
    foreign_scope = MemoryScope("fixture-local", "unrelated")
    initial = SQLiteMemoryStore(path, clock_ms=lambda: 100)
    local = initial.put(
        MemoryWrite(local_scope, "local-source", "local-due", expires_at_ms=150)
    )
    foreign = initial.put(
        MemoryWrite(foreign_scope, "foreign-source", "foreign-due", expires_at_ms=150)
    )
    with closing(sqlite3.connect(path)) as conn, conn:
        conn.execute(
            f"UPDATE memories SET {column}=CAST(? AS BLOB) WHERE memory_id=?",
            ("synthetic-corruption", foreign.memory_id),
        )

    cold = SQLiteMemoryStore(path, clock_ms=lambda: 200)
    assert cold.purge_expired(scope=local_scope) == 1
    assert cold.get(local.memory_id, local_scope, include_expired=True) is None
    assert [event.operation for event in cold.events(local_scope)] == [
        "create", "expire",
    ]
    with closing(sqlite3.connect(path)) as conn:
        assert conn.execute(
            f"SELECT typeof({column}) FROM memories WHERE memory_id=?",
            (foreign.memory_id,),
        ).fetchone() == ("blob",)
        assert conn.execute(
            "SELECT COUNT(*) FROM memory_events"
        ).fetchone() == (3,)
