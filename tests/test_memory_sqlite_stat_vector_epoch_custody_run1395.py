"""Run1395: Memory SQLite path admission retains its complete stat-policy epoch."""

from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace

import pytest

from ark.memory import MemorySchemaError, sqlite_store


def _replace_stat_aliases(
    monkeypatch: pytest.MonkeyPatch,
    predicate_calls: list[str],
) -> None:
    def hostile(name: str):
        def reject(*_args: object, **_kwargs: object) -> bool:
            predicate_calls.append(name)
            raise AssertionError("replacement stat predicate executed")

        return reject

    is_dir = hostile("S_ISDIR")
    is_link = hostile("S_ISLNK")
    is_regular = hostile("S_ISREG")
    file_type = hostile("S_IFMT")
    fake_stat = SimpleNamespace(
        S_ISDIR=is_dir,
        S_ISLNK=is_link,
        S_ISREG=is_regular,
        S_IFMT=file_type,
    )
    forged_epoch = (
        fake_stat,
        is_dir,
        is_link,
        is_regular,
        file_type,
        sqlite_store._ORIGINAL_FILE_ATTRIBUTE_REPARSE_POINT,
        sqlite_store._ORIGINAL_REPARSE_POINT_CHECK,
    )
    monkeypatch.setattr(sqlite_store, "stat", fake_stat)
    monkeypatch.setattr(sqlite_store, "_ORIGINAL_STAT", fake_stat)
    monkeypatch.setattr(sqlite_store, "_ORIGINAL_STAT_S_ISDIR", is_dir)
    monkeypatch.setattr(sqlite_store, "_ORIGINAL_STAT_S_ISLNK", is_link)
    monkeypatch.setattr(sqlite_store, "_ORIGINAL_STAT_S_ISREG", is_regular)
    monkeypatch.setattr(sqlite_store, "_ORIGINAL_STAT_IFMT", file_type)
    monkeypatch.setattr(sqlite_store, "_ORIGINAL_MEMORY_PATH_POLICY_EPOCH", forged_epoch)


def test_joint_stat_module_aliases_and_epoch_are_denied_before_lstat(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    predicate_calls: list[str] = []
    _replace_stat_aliases(monkeypatch, predicate_calls)

    def forbidden_lstat(_path: Path):
        raise AssertionError("filesystem inspected before stat-policy denial")

    monkeypatch.setattr(Path, "lstat", forbidden_lstat)
    with pytest.raises(MemorySchemaError, match="path admission policy changed"):
        sqlite_store._require_safe_memory_path(
            tmp_path / "memory.sqlite",
            create=True,
        )

    assert predicate_calls == []


def test_joint_stat_module_aliases_and_epoch_replaced_from_lstat_are_denied(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    original_lstat = Path.lstat
    predicate_calls: list[str] = []

    def reentrant_lstat(path: Path):
        metadata = original_lstat(path)
        if path == tmp_path:
            _replace_stat_aliases(monkeypatch, predicate_calls)
        return metadata

    monkeypatch.setattr(Path, "lstat", reentrant_lstat)
    with pytest.raises(MemorySchemaError, match="path admission policy changed"):
        sqlite_store._require_safe_memory_path(
            tmp_path / "memory.sqlite",
            create=True,
        )

    assert predicate_calls == []
