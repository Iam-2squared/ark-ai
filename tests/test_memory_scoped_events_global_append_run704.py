"""Scoped Memory v1 event reads refuse global append gaps before disclosure.

Only disposable local SQLite fixtures are involved; sqlite_sequence is not
authenticated provenance, an erasure witness, or external action authority.
"""

import sqlite3

import pytest

from ark.memory import MemorySchemaError, MemoryScope, MemoryWrite, SQLiteMemoryStore


def _store(tmp_path):
    store = SQLiteMemoryStore(tmp_path / "scoped-events.sqlite", clock_ms=lambda: 101)
    own = MemoryScope("owner-a", "notes")
    other = MemoryScope("owner-b", "private")
    return store, own, other


@pytest.mark.parametrize("missing_id", (1, 2, 3))
def test_missing_foreign_event_refuses_even_empty_scope(tmp_path, missing_id):
    store, own, other = _store(tmp_path)
    for index in range(3):
        store.put(MemoryWrite(other, f"foreign-{index}", "private fixture"))
    assert store.events(own) == []
    with sqlite3.connect(store.path) as conn:
        conn.execute("DELETE FROM memory_events WHERE event_id=?", (missing_id,))
    with pytest.raises(MemorySchemaError, match="global memory event append high-water"):
        store.events(own)


def test_deleted_only_event_is_detected_by_autoincrement_tail(tmp_path):
    store, own, other = _store(tmp_path)
    store.put(MemoryWrite(other, "foreign", "private fixture"))
    with sqlite3.connect(store.path) as conn:
        conn.execute("DELETE FROM memory_events")
    with pytest.raises(MemorySchemaError, match="global memory event append high-water"):
        store.events(own)


def test_locally_forged_sequence_is_rejected_before_scoped_history(tmp_path):
    store, own, other = _store(tmp_path)
    store.put(MemoryWrite(other, "foreign", "private fixture"))
    with sqlite3.connect(store.path) as conn:
        conn.execute(
            "UPDATE sqlite_sequence SET seq=9 WHERE name='memory_events'"
        )
    with pytest.raises(MemorySchemaError, match="global memory event append high-water"):
        store.events(own)


def test_intact_cross_owner_history_paginates_without_disclosing_foreign(tmp_path):
    store, own, other = _store(tmp_path)
    assert store.events(own) == []
    store.put(MemoryWrite(other, "foreign", "secret-not-to-disclose"))
    first = store.put(MemoryWrite(own, "first", "own content"))
    store.put(MemoryWrite(other, "second-foreign", "other secret"))
    second = store.put(MemoryWrite(own, "second", "own next"))
    page = store.events(own, limit=1)
    assert [event.memory_id for event in page] == [first.memory_id]
    tail = store.events(own, after_event_id=page[-1].event_id)
    assert [event.memory_id for event in tail] == [second.memory_id]
    assert "secret-not-to-disclose" not in repr(page + tail)
