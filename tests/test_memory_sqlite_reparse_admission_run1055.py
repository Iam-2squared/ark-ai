"""Memory SQLite path admission rejects Windows reparse points.

Synthetic stat metadata only: no privileged junctions or private databases.
"""

from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace

import pytest

from ark.memory import MemorySchemaError, MemoryScope, SQLiteMemoryStore, sqlite_store


def _store(path: Path) -> SQLiteMemoryStore:
    return SQLiteMemoryStore(path, clock_ms=lambda: 1_000)


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


def _forbid_sqlite_open(monkeypatch) -> None:
    def forbidden_connect(*_args, **_kwargs):
        raise AssertionError("reparse-point path reached SQLite open")

    monkeypatch.setattr(sqlite_store.sqlite3, "connect", forbidden_connect)


def test_memory_rejects_reparse_point_ancestor_before_sqlite_open(
    tmp_path: Path, monkeypatch,
) -> None:
    path = tmp_path / "nested" / "memory.sqlite"
    store = _store(path)
    _mark_reparse_point(monkeypatch, path.parent)
    _forbid_sqlite_open(monkeypatch)

    with pytest.raises(MemorySchemaError, match="ancestor refused"):
        store.events(MemoryScope("synthetic-owner"))


def test_memory_rejects_reparse_point_main_database_before_sqlite_open(
    tmp_path: Path, monkeypatch,
) -> None:
    path = tmp_path / "memory.sqlite"
    store = _store(path)
    _mark_reparse_point(monkeypatch, path)
    _forbid_sqlite_open(monkeypatch)

    with pytest.raises(MemorySchemaError, match="single regular file"):
        store.events(MemoryScope("synthetic-owner"))


def test_memory_rejects_reparse_point_sqlite_sidecar_before_sqlite_open(
    tmp_path: Path, monkeypatch,
) -> None:
    path = tmp_path / "memory.sqlite"
    store = _store(path)
    sidecar = path.with_name(path.name + "-journal")
    sidecar.write_bytes(b"synthetic sidecar marker")
    _mark_reparse_point(monkeypatch, sidecar)
    _forbid_sqlite_open(monkeypatch)

    with pytest.raises(MemorySchemaError, match="single regular file"):
        store.events(MemoryScope("synthetic-owner"))


def test_memory_reparse_policy_rebinding_is_denied_before_lstat(
    tmp_path: Path, monkeypatch,
) -> None:
    def forbidden_lstat(_path):
        raise AssertionError("changed path policy reached filesystem")

    monkeypatch.setattr(sqlite_store, "_is_reparse_point", lambda _info: False)
    monkeypatch.setattr(Path, "lstat", forbidden_lstat)

    with pytest.raises(MemorySchemaError, match="path admission policy changed"):
        sqlite_store._require_safe_memory_path(
            tmp_path / "memory.sqlite", create=True,
        )


def test_memory_reparse_attribute_requires_exact_integer() -> None:
    assert sqlite_store._is_reparse_point(
        SimpleNamespace(st_file_attributes=0x400)
    )
    assert not sqlite_store._is_reparse_point(
        SimpleNamespace(st_file_attributes=0)
    )
    # bool is an int subclass, but is not an exact stat attribute carrier.
    # Invalid metadata fails closed as a reparse-point denial.
    assert sqlite_store._is_reparse_point(
        SimpleNamespace(st_file_attributes=True)
    )
