"""Run1199: SQLite Memory cannot be redirected to another valid private store."""

from __future__ import annotations

import sqlite3
from pathlib import Path

import pytest

from ark.memory import MemorySchemaError, MemoryScope, MemoryWrite, SQLiteMemoryStore
from ark.memory import sqlite_store


def _stores(tmp_path: Path):
    scope = MemoryScope("same-owner", "private")
    original_path = tmp_path / "original.sqlite"
    foreign_path = tmp_path / "foreign.sqlite"
    original = SQLiteMemoryStore(original_path, clock_ms=lambda: 100)
    foreign = SQLiteMemoryStore(foreign_path, clock_ms=lambda: 100)
    own = original.put(MemoryWrite(scope, "profile", "original private fixture"))
    other = foreign.put(MemoryWrite(scope, "profile", "foreign private fixture"))
    return original, foreign, scope, own, other


def test_rebind_to_another_valid_private_store_is_denied_before_path_io(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    original, foreign, scope, own, other = _stores(tmp_path)
    original.path = foreign.path
    foreign_record = foreign.get(other.memory_id, scope)
    touched: list[Path] = []

    def forbidden_lstat(path: Path):
        touched.append(path)
        raise AssertionError("rebound path must be denied before filesystem inspection")

    monkeypatch.setattr(Path, "lstat", forbidden_lstat)
    with pytest.raises(MemorySchemaError, match="path identity changed"):
        original.get(own.memory_id, scope)

    assert touched == []
    assert foreign_record == other
    assert own.content == "original private fixture"


def test_equal_value_new_path_object_is_denied_before_write(tmp_path: Path) -> None:
    original, _, scope, own, _ = _stores(tmp_path)
    retained_path = original.path
    original.path = Path(str(retained_path))

    with pytest.raises(MemorySchemaError, match="path identity changed"):
        original.put(MemoryWrite(scope, "profile", "must not be written"))

    cold = SQLiteMemoryStore(retained_path, clock_ms=lambda: 200)
    assert cold.get(own.memory_id, scope) == own
    assert [event.operation for event in cold.events(scope)] == ["create"]


def test_path_identity_slot_cannot_be_reassigned_deleted_or_shadowed(
    tmp_path: Path,
) -> None:
    original, foreign, scope, _, _ = _stores(tmp_path)

    with pytest.raises(AttributeError, match="path identity is immutable"):
        original._path_identity = foreign.path
    with pytest.raises(AttributeError, match="path identity is immutable"):
        del original._path_identity

    # The slot is a data descriptor; a same-named __dict__ entry cannot
    # shadow the constructor-selected Path object.
    original.__dict__["_path_identity"] = foreign.path
    saved = original.put(MemoryWrite(scope, "second", "local"))
    assert original.get(saved.memory_id, scope).content == "local"


def test_reentrant_path_rebind_during_lstat_is_denied_before_sqlite_open(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    original, foreign, scope, own, _ = _stores(tmp_path)
    original_lstat = Path.lstat
    rebound = False

    def reentrant_lstat(path: Path):
        nonlocal rebound
        metadata = original_lstat(path)
        if not rebound and path == tmp_path:
            rebound = True
            original.path = foreign.path
        return metadata

    monkeypatch.setattr(Path, "lstat", reentrant_lstat)
    connect_calls: list[object] = []
    real_connect = sqlite_store.sqlite3.connect

    def observed_connect(*args, **kwargs):
        connect_calls.append(args[0] if args else None)
        return real_connect(*args, **kwargs)

    monkeypatch.setattr(sqlite_store.sqlite3, "connect", observed_connect)
    with pytest.raises(MemorySchemaError, match="path identity changed"):
        original.get(own.memory_id, scope)

    assert rebound is True
    assert connect_calls == []


def test_path_rebind_from_sqlite_open_callback_closes_untrusted_handle(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    original, foreign, scope, own, _ = _stores(tmp_path)
    real_connect = sqlite_store.sqlite3.connect
    opened: list[sqlite3.Connection] = []
    opened_paths: list[str] = []

    def reentrant_connect(*args, **kwargs):
        connection = real_connect(*args, **kwargs)
        opened.append(connection)
        opened_paths.append(connection.execute("PRAGMA database_list").fetchone()[2])
        original.path = foreign.path
        return connection

    monkeypatch.setattr(sqlite_store.sqlite3, "connect", reentrant_connect)
    with pytest.raises(MemorySchemaError, match="path identity changed"):
        original.get(own.memory_id, scope)

    assert len(opened) == 1
    assert opened_paths[0].endswith("original.sqlite")
    with pytest.raises(sqlite3.ProgrammingError, match="closed"):
        opened[0].execute("SELECT 1")
