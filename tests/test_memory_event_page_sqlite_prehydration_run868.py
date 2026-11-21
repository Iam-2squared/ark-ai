"""Local Memory event-page SQL admission, not authenticated history or consent."""

from __future__ import annotations

import sqlite3

import pytest

from ark.memory import MemoryScope, MemoryWrite, SQLiteMemoryStore
from ark.memory.contracts import MemorySchemaError


def _seed(tmp_path):
    store = SQLiteMemoryStore(tmp_path / "memory.sqlite", clock_ms=lambda: 100)
    scope = MemoryScope("fixture-owner")
    store.put(MemoryWrite(scope, "synthetic-one", "synthetic-data"))
    return store, scope


@pytest.mark.parametrize(
    ("column", "replacement"),
    (
        ("memory_id", sqlite3.Binary(b"mem_" + b"a" * 64)),
        ("memory_id", "mem_" + "é" * 64),
        ("memory_id", "mem_" + "a" * 4096),
        ("revision", "not-an-integer"),
        ("revision", 1.5),
        ("occurred_at_ms", "not-an-integer"),
        ("occurred_at_ms", 1.5),
    ),
)
def test_event_read_refuses_bad_sqlite_page_before_python_hydration(
    tmp_path, column, replacement,
):
    store, scope = _seed(tmp_path)
    with sqlite3.connect(store.path) as conn:
        assert conn.execute(
            f"UPDATE memory_events SET {column}=? WHERE event_id=1",
            (replacement,),
        ).rowcount == 1

    with pytest.raises(MemorySchemaError, match="page hydration admission"):
        store.events(scope)


def test_page_admission_is_scoped_and_respects_pagination(tmp_path):
    store, scope = _seed(tmp_path)
    second = MemoryScope("fixture-other-owner")
    store.put(MemoryWrite(second, "synthetic-two", "synthetic-data"))
    first_page = store.events(scope, limit=1)
    assert len(first_page) == 1
    assert first_page[0].event_id == 1

    with sqlite3.connect(store.path) as conn:
        conn.execute(
            "UPDATE memory_events SET revision=? WHERE event_id=2",
            ("invalid",),
        )
    # A local event with another owner is not hydrated by this scoped query.
    assert store.events(scope) == first_page
    with pytest.raises(MemorySchemaError, match="page hydration admission"):
        store.events(second)


def test_page_two_rejects_changed_row_without_exposing_it(tmp_path):
    store, scope = _seed(tmp_path)
    store.put(MemoryWrite(scope, "synthetic-two", "synthetic-data"))
    first = store.events(scope, limit=1)
    with sqlite3.connect(store.path) as conn:
        conn.execute(
            "UPDATE memory_events SET occurred_at_ms=? WHERE event_id=2",
            ("invalid",),
        )
    assert store.events(scope, limit=1) == first
    with pytest.raises(MemorySchemaError, match="page hydration admission"):
        store.events(scope, after_event_id=1, limit=1)
