"""Bounded expiry must not let an off-page malformed row poison a due page.

A synthetic on-disk storage-class edit is intentionally outside the Memory
contract. These tests never repair foreign or local corrupted data and do not
treat a local expiry clock as an authenticated retention decision.
"""

from __future__ import annotations

import sqlite3
from contextlib import closing

import pytest

from ark.memory import MemoryScope, MemoryWrite, SQLiteMemoryStore
from ark.memory.contracts import MemorySchemaError


@pytest.mark.parametrize("column", ("content", "metadata_json", "source_id"))
@pytest.mark.parametrize("limit", (1, 2))
def test_corrupt_second_due_row_is_confined_to_selected_page(
    tmp_path, column: str, limit: int,
) -> None:
    path = tmp_path / "due-page-atomicity.sqlite3"
    scope = MemoryScope("synthetic-due-owner", "private")
    initial = SQLiteMemoryStore(path, clock_ms=lambda: 100)
    records = [
        initial.put(MemoryWrite(scope, source, "synthetic", expires_at_ms=150))
        for source in ("first", "second")
    ]
    healthy, corrupted = sorted(records, key=lambda record: record.memory_id)
    with closing(sqlite3.connect(path)) as conn, conn:
        conn.execute(
            f"UPDATE memories SET {column}=CAST(? AS BLOB) WHERE memory_id=?",
            ("fixture-invalid-storage-class", corrupted.memory_id),
        )

    cold = SQLiteMemoryStore(path, clock_ms=lambda: 200)
    if limit == 1:
        # Only the first sorted due row may be hydrated and removed.
        assert cold.purge_expired(scope=scope, limit=1) == 1
        assert cold.get(healthy.memory_id, scope, include_expired=True) is None
    else:
        # A corrupt row *inside* the page aborts the entire transaction.
        with pytest.raises(MemorySchemaError):
            cold.purge_expired(scope=scope, limit=2)
        assert cold.get(healthy.memory_id, scope, include_expired=True) is not None

    # Recheck the selected page: both the next single-row page and the
    # original two-row page contain the malformed row and must fail closed.
    with pytest.raises(MemorySchemaError):
        cold.purge_expired(scope=scope, limit=limit)

    expected_ops = ["create", "create"] + (["expire"] if limit == 1 else [])
    assert [event.operation for event in cold.events(scope)] == expected_ops
    with closing(sqlite3.connect(path)) as conn:
        assert conn.execute(
            f"SELECT typeof({column}) FROM memories WHERE memory_id=?",
            (corrupted.memory_id,),
        ).fetchone() == ("blob",)
        expected_count = 1 if limit == 1 else 2
        assert conn.execute("SELECT COUNT(*) FROM memories").fetchone() == (
            expected_count,
        )
        assert conn.execute(
            "SELECT COUNT(*) FROM memory_events"
        ).fetchone() == (len(expected_ops),)

    # Cold restart retains exactly the same transaction boundary.
    reopened = SQLiteMemoryStore(path, clock_ms=lambda: 201)
    assert [event.operation for event in reopened.events(scope)] == expected_ops
    with pytest.raises(MemorySchemaError):
        reopened.purge_expired(scope=scope, limit=limit)
