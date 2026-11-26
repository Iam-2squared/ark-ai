"""The frozen Memory v1 DDL oracle cannot leak SQLite handles.

These are disposable in-memory schemas, not evidence of production database
provenance or permission to mutate a protected memory store.
"""

from __future__ import annotations

import sqlite3
from contextlib import closing

import pytest

import ark.memory.sqlite_store as memory


def _fixture() -> sqlite3.Connection:
    conn = sqlite3.connect(":memory:")
    conn.executescript(memory._SCHEMA_V1_SQL)
    return conn


def _track_oracle(monkeypatch):
    seen: list[sqlite3.Connection] = []
    original = memory.closing

    def tracked(conn):
        seen.append(conn)
        return original(conn)

    monkeypatch.setattr(memory, "closing", tracked)
    return seen


def _assert_closed(seen: list[sqlite3.Connection]) -> None:
    assert len(seen) == 1
    with pytest.raises(sqlite3.ProgrammingError, match="closed"):
        seen[0].execute("SELECT 1")


def test_memory_schema_oracle_closes_on_valid_frozen_ddl(monkeypatch) -> None:
    with closing(_fixture()) as conn:
        seen = _track_oracle(monkeypatch)
        memory._validate_v1_schema(conn)
        _assert_closed(seen)


def test_memory_schema_oracle_closes_on_foreign_index(monkeypatch) -> None:
    with closing(_fixture()) as conn:
        conn.execute("DROP INDEX idx_mem_expiry")
        conn.execute("CREATE INDEX idx_mem_expiry ON memories(updated_at_ms)")
        seen = _track_oracle(monkeypatch)
        with pytest.raises(memory.MemorySchemaError, match="frozen DDL"):
            memory._validate_v1_schema(conn)
        _assert_closed(seen)


def test_memory_schema_oracle_closes_when_catalog_raises(
    monkeypatch,
) -> None:
    with closing(_fixture()) as conn:
        seen = _track_oracle(monkeypatch)

        def fail_catalog(_conn):
            raise RuntimeError("synthetic memory catalog fault")

        monkeypatch.setattr(memory, "_schema_objects", fail_catalog)
        with pytest.raises(RuntimeError, match="synthetic memory catalog fault"):
            memory._validate_v1_schema(conn)
        _assert_closed(seen)
