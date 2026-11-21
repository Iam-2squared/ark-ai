"""Run957: mutation SQL prehydration refuses stored scalar-class corruption.

Synthetic tampering is used only in a fresh temporary SQLite fixture. No
frozen schema migration, data repair, disclosure or permission is performed.
"""

from __future__ import annotations

import sqlite3

import pytest

from ark.memory import MemorySchemaError, MemoryScope, MemoryWrite, SQLiteMemoryStore


@pytest.mark.parametrize(
    ("column", "corrupted"),
    (
        ("owner_id", sqlite3.Binary(b"foreign-owner")),
        ("namespace", sqlite3.Binary(b"private")),
        ("source_id", sqlite3.Binary(b"source")),
        ("expires_at_ms", sqlite3.Binary(b"100")),
        ("revision", sqlite3.Binary(b"1")),
        ("content_sha256", "a" * 63),
    ),
)
def test_corrupt_target_scalar_admission_denies_cold_put_and_delete(
    tmp_path, column: str, corrupted: object,
) -> None:
    path = tmp_path / "synthetic-mutator-scalar.sqlite"
    scope = MemoryScope("synthetic-owner", "private")
    initial = SQLiteMemoryStore(path, clock_ms=lambda: 100)
    row = initial.put(MemoryWrite(scope, "source", "synthetic-private-content"))
    with sqlite3.connect(path) as conn:
        conn.execute(
            f"UPDATE memories SET {column}=? WHERE memory_id=?",
            (corrupted, row.memory_id),
        )
        before = conn.execute(
            "SELECT * FROM memories WHERE memory_id=?", (row.memory_id,),
        ).fetchone()
        events_before = conn.execute(
            "SELECT * FROM memory_events ORDER BY event_id",
        ).fetchall()

    # A new handle must not silently replace/delete the malformed target
    # using a matching deterministic memory ID and the old revision.
    cold = SQLiteMemoryStore(path, clock_ms=lambda: 101)
    with pytest.raises(MemorySchemaError):
        cold.put(
            MemoryWrite(scope, "source", "would-be-update"),
            expected_revision=1,
        )
    with pytest.raises(MemorySchemaError):
        cold.delete(row.memory_id, scope, expected_revision=1)

    with sqlite3.connect(path) as conn:
        assert conn.execute(
            "SELECT * FROM memories WHERE memory_id=?", (row.memory_id,),
        ).fetchone() == before
        assert conn.execute(
            "SELECT * FROM memory_events ORDER BY event_id",
        ).fetchall() == events_before


def test_valid_scalar_and_expiry_update_remains_compatible(tmp_path) -> None:
    path = tmp_path / "healthy-mutator-scalar.sqlite"
    scope = MemoryScope("owner", "private")
    first = SQLiteMemoryStore(path, clock_ms=lambda: 100).put(
        MemoryWrite(scope, "source", "content", expires_at_ms=250),
    )
    assert first.revision == 1
    assert first.expires_at_ms == 250
    cold = SQLiteMemoryStore(path, clock_ms=lambda: 110)
    second = cold.put(
        MemoryWrite(scope, "source", "changed", expires_at_ms=300),
        expected_revision=1,
    )
    assert second.revision == 2
    assert second.expires_at_ms == 300
    assert cold.delete(second.memory_id, scope, expected_revision=2) is True
    assert [event.operation for event in cold.events(scope)] == [
        "create", "update", "delete",
    ]
