"""Synthetic v1 mutation regression: corrupted stored rows never become CAS authority."""

import sqlite3

import pytest

from ark.memory.contracts import MemorySchemaError, MemoryScope, MemoryWrite
from ark.memory.sqlite_store import SQLiteMemoryStore


def _fixture(tmp_path, *, expiry=None):
    path = tmp_path / "memory.sqlite3"
    scope = MemoryScope("synthetic-owner", "synthetic-namespace")
    store = SQLiteMemoryStore(path, clock_ms=lambda: 100)
    write = MemoryWrite(scope, "source", "original", expires_at_ms=expiry)
    record = store.put(write)
    return path, scope, store, write, record


def _tamper(path, column, value):
    with sqlite3.connect(path) as conn:
        conn.execute(f"UPDATE memories SET {column}=?", (value,))


@pytest.mark.parametrize(
    ("column", "value"),
    [
        ("revision", sqlite3.Binary(b"1")),
        ("created_at_ms", sqlite3.Binary(b"100")),
        ("content_sha256", "0" * 64),
    ],
)
def test_put_rejects_corrupt_stored_state_before_cas(tmp_path, column, value):
    path, scope, store, _, record = _fixture(tmp_path)
    _tamper(path, column, value)
    with pytest.raises(MemorySchemaError):
        store.put(MemoryWrite(scope, "source", "replacement"), expected_revision=1)
    with sqlite3.connect(path) as conn:
        assert conn.execute("SELECT content FROM memories").fetchone()[0] == "original"
    assert [event.operation for event in store.events(scope)] == ["create"]


@pytest.mark.parametrize(
    ("column", "value"),
    [
        ("revision", sqlite3.Binary(b"1")),
        ("updated_at_ms", sqlite3.Binary(b"100")),
        ("metadata_json", '{"bad": 2}'),
    ],
)
def test_delete_rejects_corrupt_stored_state_before_cas(tmp_path, column, value):
    path, scope, store, _, record = _fixture(tmp_path)
    _tamper(path, column, value)
    with pytest.raises(MemorySchemaError):
        store.delete(record.memory_id, scope, expected_revision=1)
    with sqlite3.connect(path) as conn:
        assert conn.execute("SELECT count(*) FROM memories").fetchone()[0] == 1
    assert [event.operation for event in store.events(scope)] == ["create"]


@pytest.mark.parametrize(
    ("column", "value"),
    [
        ("revision", sqlite3.Binary(b"1")),
        ("content_sha256", "0" * 64),
        ("source_id", "wrong-preimage"),
    ],
)
def test_purge_rejects_corrupt_expired_row_without_any_deletion(tmp_path, column, value):
    path, scope, store, _, record = _fixture(tmp_path, expiry=90)
    _tamper(path, column, value)
    with pytest.raises(MemorySchemaError):
        store.purge_expired(scope=scope)
    with sqlite3.connect(path) as conn:
        assert conn.execute("SELECT count(*) FROM memories").fetchone()[0] == 1
    assert [event.operation for event in store.events(scope)] == ["create"]


def test_valid_v1_mutations_still_increment_revision_and_emit_events(tmp_path):
    _, scope, store, write, record = _fixture(tmp_path)
    revised = store.put(write, expected_revision=record.revision)
    assert revised.revision == 2
    assert store.delete(revised.memory_id, scope, expected_revision=2)
    assert [item.operation for item in store.events(scope)] == [
        "create", "update", "delete"
    ]
