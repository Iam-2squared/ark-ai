"""Run1094: scoped Memory event reads validate the global frontier before hydration.

Disposable synthetic SQLite only. A local high-water check is not authenticated
history, independent custody, trusted time, consent, or action authority.
"""

from __future__ import annotations

import sqlite3

import pytest

from ark.memory import MemorySchemaError, MemoryScope, MemoryWrite, SQLiteMemoryStore


@pytest.mark.parametrize("corruption", ("foreign-gap", "duplicate-sequence"))
def test_scoped_event_read_rejects_global_frontier_before_row_hydration(
    tmp_path, monkeypatch: pytest.MonkeyPatch, corruption: str,
) -> None:
    path = tmp_path / "memory.sqlite3"
    primary = MemoryScope("synthetic-primary", "private")
    foreign = MemoryScope("synthetic-foreign", "private")
    store = SQLiteMemoryStore(path, clock_ms=lambda: 100)
    first = store.put(MemoryWrite(primary, "primary", "synthetic one"))
    store.put(MemoryWrite(foreign, "foreign", "synthetic two"))
    store.put(
        MemoryWrite(primary, "primary", "synthetic update"),
        expected_revision=first.revision,
    )

    with sqlite3.connect(path) as conn:
        assert conn.execute(
            "SELECT event_id FROM memory_events ORDER BY event_id"
        ).fetchall() == [(1,), (2,), (3,)]
        if corruption == "foreign-gap":
            conn.execute("DELETE FROM memory_events WHERE event_id=2")
        else:
            # sqlite_sequence.name is not unique. A duplicate marker must not
            # be accepted by a first-row-only high-water check.
            conn.execute(
                "INSERT INTO sqlite_sequence(name,seq) VALUES(?,?)",
                ("memory_events", 3),
            )

    hydrated_pages: list[str] = []
    original_connect = SQLiteMemoryStore._connect_readonly

    def traced_connect(self: SQLiteMemoryStore) -> sqlite3.Connection:
        conn = original_connect(self)
        conn.set_trace_callback(
            lambda sql: hydrated_pages.append(sql)
            if sql.lstrip().upper().startswith("SELECT * FROM MEMORY_EVENTS")
            else None
        )
        return conn

    with monkeypatch.context() as patch:
        patch.setattr(SQLiteMemoryStore, "_connect_readonly", traced_connect)
        with pytest.raises(
            MemorySchemaError, match="global memory event append high-water mismatch",
        ):
            store.events(primary)

    # The global event frontier is checked in the same read transaction before
    # any scope-specific SELECT * can materialize private event rows.
    assert hydrated_pages == []
