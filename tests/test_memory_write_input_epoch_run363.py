"""Synthetic Memory v1 reentrant-clock CAS input immutability regressions."""

import sqlite3

import pytest

from ark.memory.contracts import MemorySchemaError, MemoryScope, MemoryWrite
from ark.memory.sqlite_store import SQLiteMemoryStore


@pytest.mark.parametrize(
    "field",
    ("content", "source_id", "expires_at_ms", "metadata", "scope", "scope_namespace"),
)
def test_create_rejects_reflected_write_change_without_persisting(tmp_path, field):
    store = SQLiteMemoryStore(tmp_path / "memory.db", clock_ms=lambda: 100)
    original_scope = MemoryScope("fixture-owner", "fixture-space")
    write = MemoryWrite(original_scope, "item", "safe", {"purpose": "fixture"})

    def mutating_clock():
        if field == "scope_namespace":
            object.__setattr__(original_scope, "namespace", "other-space")
        else:
            replacement = {
                "content": "changed",
                "source_id": "other",
                "expires_at_ms": 900,
                "metadata": {"purpose": "other"},
                "scope": MemoryScope("other-owner", "fixture-space"),
            }[field]
            object.__setattr__(write, field, replacement)
        return 101

    store._clock_ms = mutating_clock
    with pytest.raises(MemorySchemaError, match="write changed during clock"):
        store.put(write)
    with sqlite3.connect(store.path) as conn:
        assert conn.execute("SELECT COUNT(*) FROM memories").fetchone()[0] == 0
        assert conn.execute("SELECT COUNT(*) FROM memory_events").fetchone()[0] == 0


@pytest.mark.parametrize("field", ("content", "metadata", "scope", "source_id"))
def test_update_rejects_reflected_write_change_and_rolls_back(tmp_path, field):
    scope = MemoryScope("fixture-owner", "fixture-space")
    store = SQLiteMemoryStore(tmp_path / "memory.db", clock_ms=lambda: 100)
    original = store.put(MemoryWrite(scope, "item", "safe"))
    write = MemoryWrite(scope, "item", "replacement", {"purpose": "fixture"})

    def mutating_clock():
        replacement = {
            "content": "changed",
            "metadata": {"purpose": "other"},
            "scope": MemoryScope("other-owner", "fixture-space"),
            "source_id": "other",
        }[field]
        object.__setattr__(write, field, replacement)
        return 101

    store._clock_ms = mutating_clock
    with pytest.raises(MemorySchemaError, match="write changed during clock"):
        store.put(write, expected_revision=original.revision)
    assert store.get(original.memory_id, scope, include_expired=True).content == "safe"
    assert [event.operation for event in store.events(scope)] == ["create"]


def test_unchanged_write_pins_returned_record_and_event(tmp_path):
    scope = MemoryScope("fixture-owner", "fixture-space")
    store = SQLiteMemoryStore(tmp_path / "memory.db", clock_ms=lambda: 100)
    write = MemoryWrite(scope, "item", "safe", {"purpose": "fixture"})
    created = store.put(write)
    assert created.content == "safe"
    assert created.metadata["purpose"] == "fixture"
    assert [event.operation for event in store.events(scope)] == ["create"]
    updated = store.put(write, expected_revision=1)
    assert updated.revision == 2
    assert updated.scope == scope
    assert [event.operation for event in store.events(scope)] == ["create", "update"]
