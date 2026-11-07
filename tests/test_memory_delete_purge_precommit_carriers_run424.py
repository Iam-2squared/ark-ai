"""Memory delete/expiry must reject reentrant equal-text scope carrier swaps.

The SQLite trace hook simulates a callback at the SELECT or audit INSERT.
Every fixture is disposable and local; failed pre-commit operations must leave
the original row and audit event intact. No external data or delete authority.
"""

import sqlite3

import pytest

from ark.memory.contracts import MemorySchemaError, MemoryScope, MemoryWrite
from ark.memory.sqlite_store import SQLiteMemoryStore


def _equal_distinct(text: str) -> str:
    replacement = ("!" + text)[1:]
    assert replacement == text and replacement is not text
    return replacement


def _inject_on_sql(store, monkeypatch, scope, field, phase):
    original_connect = store._connect
    callback_hits = []

    def connected(*, create=False):
        conn = original_connect(create=create)

        def on_statement(sql):
            normalized = " ".join(sql.upper().split())
            match = (
                "SELECT * FROM MEMORIES" in normalized
                if phase == "select"
                else "INSERT INTO MEMORY_EVENTS" in normalized
            )
            if match and not callback_hits:
                original = getattr(scope, field)
                object.__setattr__(scope, field, _equal_distinct(original))
                callback_hits.append(phase)

        conn.set_trace_callback(on_statement)
        return conn

    monkeypatch.setattr(store, "_connect", connected)
    return callback_hits


@pytest.mark.parametrize("operation", ("delete", "purge"))
@pytest.mark.parametrize("phase", ("select", "event"))
@pytest.mark.parametrize("field", ("owner_id", "namespace"))
def test_equal_value_scope_swap_rolls_back_before_commit(
    tmp_path, monkeypatch, operation, phase, field,
):
    path = tmp_path / "memory.sqlite"
    store = SQLiteMemoryStore(path, clock_ms=lambda: 100)
    scope = MemoryScope("fixture-owner", "fixture-namespace")
    record = store.put(
        MemoryWrite(scope, "fixture", "private-local", expires_at_ms=99)
    )
    hits = _inject_on_sql(store, monkeypatch, scope, field, phase)
    with pytest.raises(MemorySchemaError, match="scope changed"):
        if operation == "delete":
            store.delete(record.memory_id, scope, expected_revision=1)
        else:
            store.purge_expired(scope=scope)
    assert hits == [phase]

    # The identity fence must run inside the transaction; detecting the drift
    # only after SQLite COMMIT would wrongly leave a durable deletion.
    with sqlite3.connect(path) as conn:
        assert conn.execute(
            "SELECT memory_id, revision FROM memories",
        ).fetchall() == [(record.memory_id, 1)]
        assert conn.execute(
            "SELECT operation, revision FROM memory_events",
        ).fetchall() == [("create", 1)]


@pytest.mark.parametrize("field", ("owner_id", "namespace"))
def test_missing_row_cannot_return_clean_false_after_scope_swap(
    tmp_path, monkeypatch, field,
):
    path = tmp_path / "memory.sqlite"
    store = SQLiteMemoryStore(path, clock_ms=lambda: 100)
    scope = MemoryScope("fixture-owner", "fixture-namespace")
    hits = _inject_on_sql(store, monkeypatch, scope, field, "select")
    with pytest.raises(MemorySchemaError, match="scope changed during read"):
        store.delete("mem_" + "a" * 64, scope, expected_revision=1)
    assert hits == ["select"]
    with sqlite3.connect(path) as conn:
        assert conn.execute("SELECT COUNT(*) FROM memory_events").fetchone() == (0,)


def test_unmodified_scoped_delete_and_expiry_still_commit_exactly_once(tmp_path):
    store = SQLiteMemoryStore(tmp_path / "memory.sqlite", clock_ms=lambda: 100)
    scope = MemoryScope("fixture-owner", "fixture-namespace")
    first = store.put(MemoryWrite(scope, "one", "private-one", expires_at_ms=99))
    store.put(MemoryWrite(scope, "two", "private-two", expires_at_ms=99))
    assert store.delete(first.memory_id, scope, expected_revision=1) is True
    assert store.purge_expired(scope=scope) == 1
    assert store.purge_expired(scope=scope) == 0
    assert [event.operation for event in store.events(scope)] == [
        "create", "create", "delete", "expire",
    ]
