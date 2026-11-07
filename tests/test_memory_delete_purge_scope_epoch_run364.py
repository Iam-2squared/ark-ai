"""Synthetic Memory v1 delete/purge scope epoch checks, never external data."""

import sqlite3

import pytest

from ark.memory.contracts import MemorySchemaError, MemoryScope, MemoryWrite
from ark.memory.sqlite_store import SQLiteMemoryStore


@pytest.mark.parametrize("operation", ("delete", "purge"))
@pytest.mark.parametrize("field", ("owner_id", "namespace"))
def test_clock_reflection_cannot_retarget_scope_or_audit(tmp_path, operation, field):
    scope = MemoryScope("synthetic-owner", "synthetic-namespace")
    store = SQLiteMemoryStore(tmp_path / "memory.sqlite3", clock_ms=lambda: 100)
    record = store.put(
        MemoryWrite(scope, "synthetic-source", "keep", expires_at_ms=90)
    )

    def changing_clock():
        object.__setattr__(scope, field, "unexpected-scope")
        return 101

    store._clock_ms = changing_clock
    with pytest.raises(MemorySchemaError, match="scope changed during clock"):
        if operation == "delete":
            store.delete(record.memory_id, scope, expected_revision=record.revision)
        else:
            store.purge_expired(scope=scope)

    with sqlite3.connect(store.path) as conn:
        assert conn.execute("SELECT COUNT(*) FROM memories").fetchone()[0] == 1
        assert conn.execute("SELECT COUNT(*) FROM memory_events").fetchone()[0] == 1
    original = MemoryScope("synthetic-owner", "synthetic-namespace")
    assert store.get(record.memory_id, original, include_expired=True).content == "keep"
    assert [event.operation for event in store.events(original)] == ["create"]


@pytest.mark.parametrize("operation", ("delete", "purge"))
def test_unchanged_scope_keeps_original_identity_and_audit(tmp_path, operation):
    scope = MemoryScope("synthetic-owner", "synthetic-namespace")
    store = SQLiteMemoryStore(tmp_path / "memory.sqlite3", clock_ms=lambda: 100)
    record = store.put(
        MemoryWrite(scope, "synthetic-source", "erase", expires_at_ms=90)
    )
    store._clock_ms = lambda: 101
    if operation == "delete":
        assert store.delete(record.memory_id, scope, expected_revision=1)
        expected = "delete"
    else:
        assert store.purge_expired(scope=scope) == 1
        expected = "expire"
    assert [event.operation for event in store.events(scope)] == ["create", expected]
    assert store.get(record.memory_id, scope, include_expired=True) is None


def test_unscoped_purge_retains_existing_behavior(tmp_path):
    store = SQLiteMemoryStore(tmp_path / "memory.sqlite3", clock_ms=lambda: 100)
    owner = MemoryScope("synthetic-owner", "synthetic-namespace")
    store.put(MemoryWrite(owner, "source", "erase", expires_at_ms=90))
    assert store.purge_expired() == 1
    assert [event.operation for event in store.events(owner)] == ["create", "expire"]


@pytest.mark.parametrize("operation", ("delete", "purge"))
def test_imitation_scope_rejected_before_clock(tmp_path, operation):
    store = SQLiteMemoryStore(tmp_path / "memory.sqlite3", clock_ms=lambda: 100)
    class Imitation:
        owner_id = "synthetic-owner"
        namespace = "synthetic-namespace"
    with pytest.raises(TypeError, match="exact MemoryScope"):
        if operation == "delete":
            store.delete("mem_" + "0" * 64, Imitation(), expected_revision=1)
        else:
            store.purge_expired(scope=Imitation())
