"""Memory SQLite open must retain the exact admitted Path object."""

from __future__ import annotations

import sqlite3
from pathlib import Path

import pytest

import ark.memory.sqlite_store as memory_module
from ark.memory.sqlite_store import MemorySchemaError, SQLiteMemoryStore


def _store(path: Path) -> SQLiteMemoryStore:
    return SQLiteMemoryStore(path, clock_ms=lambda: 100)


@pytest.mark.parametrize("method", ["_connect", "_connect_readonly"])
@pytest.mark.parametrize("replacement_kind", ["equal", "different"])
def test_memory_open_rejects_rebound_path_and_closes_original_handle(
    tmp_path: Path, monkeypatch, method: str, replacement_kind: str,
) -> None:
    store = _store(tmp_path / "primary.sqlite")
    original_path = store.path
    if replacement_kind == "equal":
        replacement = Path(str(original_path))
        assert replacement == original_path
        assert replacement is not original_path
    else:
        replacement = _store(tmp_path / "replacement.sqlite").path
        assert replacement != original_path

    original_connect = memory_module.sqlite3.connect
    opened = []

    def rebind_path_after_open(*args, **kwargs):
        connection = original_connect(*args, **kwargs)
        opened.append(connection)
        # Simulate a reentrant source replacement after SQLite has opened the
        # original database but before the post-open pathname check.
        store.path = replacement
        return connection

    monkeypatch.setattr(
        memory_module.sqlite3, "connect", rebind_path_after_open,
    )
    with pytest.raises(MemorySchemaError, match="path changed during"):
        getattr(store, method)()

    assert len(opened) == 1
    with pytest.raises(sqlite3.ProgrammingError, match="closed"):
        opened[0].execute("SELECT 1")
