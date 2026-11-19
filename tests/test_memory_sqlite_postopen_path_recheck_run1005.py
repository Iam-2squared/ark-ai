"""Memory SQLite opens recheck path admission before any query or PRAGMA."""

from __future__ import annotations

import sqlite3
from pathlib import Path
from types import SimpleNamespace

import pytest

from ark.memory import MemorySchemaError, MemoryScope, MemoryWrite, SQLiteMemoryStore, sqlite_store


def _mark_reparse_point(monkeypatch, target: Path) -> None:
    original_lstat = Path.lstat

    def marked_lstat(path):
        info = original_lstat(path)
        if path == target:
            return SimpleNamespace(
                st_mode=info.st_mode,
                st_nlink=info.st_nlink,
                st_file_attributes=0x400,
            )
        return info

    monkeypatch.setattr(Path, "lstat", marked_lstat)


@pytest.mark.parametrize("operation", ("read", "write"))
def test_memory_closes_connection_when_path_changes_after_sqlite_open(
    tmp_path: Path, monkeypatch, operation: str,
) -> None:
    path = tmp_path / "memory.sqlite"
    store = SQLiteMemoryStore(path, clock_ms=lambda: 1_000)
    scope = MemoryScope("synthetic-owner", "private")
    original_connect = sqlite_store.sqlite3.connect
    opened = []

    def open_then_reparse(*args, **kwargs):
        connection = original_connect(*args, **kwargs)
        opened.append(connection)
        # The pre-open lstat passed. Simulate the same path becoming a
        # reparse point before SQLite's connection is returned to its caller.
        _mark_reparse_point(monkeypatch, path)
        return connection

    monkeypatch.setattr(sqlite_store.sqlite3, "connect", open_then_reparse)

    with pytest.raises(MemorySchemaError, match="single regular file"):
        if operation == "read":
            store.events(scope)
        else:
            store.put(MemoryWrite(scope, "source", "synthetic content"))

    assert len(opened) == 1
    with pytest.raises(sqlite3.ProgrammingError):
        opened[0].execute("SELECT 1")
