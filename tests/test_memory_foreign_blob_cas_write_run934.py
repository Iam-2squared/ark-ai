"""Foreign corrupted Memory rows do not become a global write quarantine.

Only disposable SQLite fixtures are modified. This verifies namespace/owner
isolation for a valid row+event CAS update, not independent custody, consent,
a general claim that arbitrary corrupt databases are safe, or actual dispatch.
"""

from __future__ import annotations

import sqlite3
from contextlib import closing

import pytest

from ark.memory import (
    MemoryConflictError,
    MemoryScope,
    MemoryWrite,
    SQLiteMemoryStore,
)


@pytest.mark.parametrize("poison_column", ("content", "metadata_json", "source_id"))
@pytest.mark.parametrize("foreign_owner", (False, True))
def test_healthy_scope_cas_survives_unselected_foreign_blob(
    tmp_path, poison_column: str, foreign_owner: bool,
) -> None:
    path = tmp_path / "scoped-cas-poison.sqlite3"
    local_scope = MemoryScope("local-owner", "private")
    foreign_scope = (
        MemoryScope("different-owner", "private") if foreign_owner
        else MemoryScope("local-owner", "unrelated")
    )
    initial = SQLiteMemoryStore(path, clock_ms=lambda: 100)
    local = initial.put(MemoryWrite(local_scope, "safe", "v1"))
    foreign = initial.put(MemoryWrite(foreign_scope, "foreign", "untouched"))

    # Persist an invalid SQLite storage class outside the selected scope.
    with closing(sqlite3.connect(path)) as conn, conn:
        conn.execute(
            f"UPDATE memories SET {poison_column}=CAST(? AS BLOB) "
            "WHERE memory_id=?",
            ("foreign-corruption", foreign.memory_id),
        )

    cold = SQLiteMemoryStore(path, clock_ms=lambda: 200)
    updated = cold.put(
        MemoryWrite(local_scope, "safe", "v2"), expected_revision=1,
    )
    assert updated.memory_id == local.memory_id
    assert updated.revision == 2
    assert updated.content == "v2"

    # Stale CAS must not make a fourth event, nor hydrate/repair foreign data.
    with pytest.raises(MemoryConflictError):
        cold.put(
            MemoryWrite(local_scope, "safe", "stale"), expected_revision=1,
        )
    assert SQLiteMemoryStore(path, clock_ms=lambda: 201).get(
        local.memory_id, local_scope, include_expired=True,
    ).content == "v2"
    assert [
        event.operation for event in cold.events(local_scope)
    ] == ["create", "update"]
    with closing(sqlite3.connect(path)) as conn:
        assert conn.execute(
            f"SELECT typeof({poison_column}) FROM memories "
            "WHERE memory_id=?",
            (foreign.memory_id,),
        ).fetchone() == ("blob",)
        assert conn.execute(
            "SELECT COUNT(*) FROM memory_events",
        ).fetchone() == (3,)
