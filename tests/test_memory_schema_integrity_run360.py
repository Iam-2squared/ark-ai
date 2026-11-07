"""Startup checks frozen Memory v1 SQLite DDL without migrations or schema changes."""

import sqlite3

import pytest

from ark.memory import MemorySchemaError, MemoryScope, MemoryWrite, SQLiteMemoryStore
from ark.memory.sqlite_store import _normalized_ddl


@pytest.mark.parametrize("tamper", ["drop_index", "replace_index", "add_trigger", "check_literal"])
def test_reopened_v1_database_rejects_altered_schema(tmp_path, tamper: str) -> None:
    path = tmp_path / "memory.sqlite3"
    store = SQLiteMemoryStore(path, clock_ms=lambda: 100)
    scope = MemoryScope("fixture-owner")
    store.put(MemoryWrite(scope, "fixture", "synthetic-content"))
    with sqlite3.connect(path) as conn:
        if tamper == "drop_index":
            conn.execute("DROP INDEX idx_mem_expiry")
        elif tamper == "replace_index":
            conn.execute("DROP INDEX idx_mem_expiry")
            conn.execute("CREATE INDEX idx_mem_expiry ON memories(expires_at_ms)")
        elif tamper == "add_trigger":
            conn.execute(
                "CREATE TRIGGER fixture_intrusion BEFORE INSERT ON memory_events "
                "BEGIN SELECT 1; END"
            )
        else:
            # Tamper with SQL text only on a disposable fixture, not on real data.
            conn.execute("PRAGMA writable_schema=ON")
            assert conn.execute(
                "UPDATE sqlite_master SET sql=replace(sql, ?, ?) WHERE name=?",
                ("'expire'", "'EXPIRE'", "memory_events"),
            ).rowcount == 1
            conn.execute("PRAGMA writable_schema=OFF")
        assert conn.execute("PRAGMA user_version").fetchone()[0] == 1
    with pytest.raises(MemorySchemaError, match="v1 schema"):
        SQLiteMemoryStore(path)


def test_untouched_schema_and_existing_rows_survive_reopen(tmp_path) -> None:
    path = tmp_path / "memory.sqlite3"
    scope = MemoryScope("fixture-owner")
    store = SQLiteMemoryStore(path, clock_ms=lambda: 100)
    record = store.put(MemoryWrite(scope, "fixture", "synthetic-content"))
    reopened = SQLiteMemoryStore(path, clock_ms=lambda: 101)
    assert reopened.get(record.memory_id, scope) == record
    assert [item.operation for item in reopened.events(scope)] == ["create"]


def test_ddl_normalizer_preserves_quoted_literal_case_and_whitespace() -> None:
    canonical = "CREATE TABLE x (op TEXT CHECK(op IN('create', 'expire')))"
    spacing = "create  table x(op text check(op in('create','expire')))"
    assert _normalized_ddl(canonical) == _normalized_ddl(spacing)
    assert _normalized_ddl(canonical) != _normalized_ddl(
        "CREATE TABLE x (op TEXT CHECK(op IN('CREATE', 'expire')))"
    )
    assert _normalized_ddl("SELECT 'a b'") != _normalized_ddl("SELECT 'ab'")
