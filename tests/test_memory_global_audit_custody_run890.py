"""Global Memory event history must remain dense across unrelated scopes.

Local synthetic SQLite corruption fixtures; no user data, tools or external I/O.
Even a scope-local page is rejected if the shared append high-water is damaged.
"""

import sqlite3

import pytest

from ark.memory import (
    MemorySchemaError,
    MemoryScope,
    MemoryWrite,
    SQLiteMemoryStore,
)


def _seed(tmp_path):
    path = tmp_path / "memory.sqlite"
    store = SQLiteMemoryStore(path, clock_ms=lambda: 100)
    first = MemoryScope("synthetic-a", "notes")
    foreign = MemoryScope("synthetic-b", "notes")
    store.put(MemoryWrite(first, "a", "synthetic-a-content"))
    store.put(MemoryWrite(foreign, "b", "synthetic-b-content"))
    return path, store, first, foreign


def test_foreign_owner_event_gap_vetoes_unrelated_scope_page_after_restart(tmp_path):
    path, store, first, foreign = _seed(tmp_path)
    assert len(store.events(first)) == 1
    assert len(store.events(foreign)) == 1
    with sqlite3.connect(path) as conn:
        assert conn.execute(
            "DELETE FROM memory_events WHERE owner_id=?", (foreign.owner_id,),
        ).rowcount == 1

    restarted = SQLiteMemoryStore(path, clock_ms=lambda: 110)
    with pytest.raises(MemorySchemaError, match="high-water"):
        restarted.events(first)
    # A read-side rejection does not restore or silently rewrite missing events.
    with sqlite3.connect(path) as conn:
        assert conn.execute("SELECT COUNT(*) FROM memory_events").fetchone() == (1,)


def test_sqlite_autoincrement_watermark_drift_fails_before_scoped_pagination(tmp_path):
    path, _store, first, _foreign = _seed(tmp_path)
    with sqlite3.connect(path) as conn:
        assert conn.execute(
            "UPDATE sqlite_sequence SET seq=seq+1 WHERE name='memory_events'",
        ).rowcount == 1

    reopened = SQLiteMemoryStore(path, clock_ms=lambda: 110)
    with pytest.raises(MemorySchemaError, match="high-water"):
        reopened.events(first, after_event_id=1, limit=1)
    with pytest.raises(MemorySchemaError, match="high-water"):
        reopened.events(first, after_event_id=100, limit=1)


def test_zero_event_rows_with_nonzero_retained_sequence_is_not_clean_genesis(tmp_path):
    path, _store, first, _foreign = _seed(tmp_path)
    with sqlite3.connect(path) as conn:
        assert conn.execute("DELETE FROM memory_events").rowcount == 2

    reopened = SQLiteMemoryStore(path, clock_ms=lambda: 110)
    with pytest.raises(MemorySchemaError, match="high-water"):
        reopened.events(first)
    with sqlite3.connect(path) as conn:
        count = conn.execute("SELECT COUNT(*) FROM memory_events").fetchone()[0]
        watermark = conn.execute(
            "SELECT seq FROM sqlite_sequence WHERE name='memory_events'",
        ).fetchone()[0]
    assert count == 0 and watermark == 2


def test_interleaved_unrelated_scopes_preserve_scope_pagination_and_global_ids(tmp_path):
    _path, store, first, foreign = _seed(tmp_path)
    store.put(
        MemoryWrite(first, "a", "synthetic-a-revision-two"),
        expected_revision=1,
    )
    a = store.events(first)
    b = store.events(foreign)
    assert [(event.event_id, event.operation) for event in a] == [
        (1, "create"), (3, "update"),
    ]
    assert [(event.event_id, event.operation) for event in b] == [(2, "create")]
    assert [event.event_id for event in store.events(first, after_event_id=1)] == [3]
