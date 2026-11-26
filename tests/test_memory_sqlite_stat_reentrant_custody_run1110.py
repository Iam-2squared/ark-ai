"""Run1110: Memory SQLite path admission pins stat policy across metadata callbacks.

Synthetic in-process substitutions only; no private database or external
filesystem alias is opened and no external effect is involved.
"""

from __future__ import annotations

import stat
from pathlib import Path

import pytest

from ark.memory import MemorySchemaError, sqlite_store


@pytest.mark.parametrize("name", ("S_ISDIR", "S_ISLNK", "S_ISREG", "S_IFMT"))
def test_stat_predicate_rebinding_is_denied_before_lstat(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, name: str,
) -> None:
    def forbidden_lstat(_path: Path):
        raise AssertionError("filesystem inspected after stat predicate substitution")

    with monkeypatch.context() as patch:
        patch.setattr(sqlite_store.stat, name, lambda *_args: True)
        patch.setattr(Path, "lstat", forbidden_lstat)
        with pytest.raises(MemorySchemaError, match="path admission policy changed"):
            sqlite_store._require_safe_memory_path(
                tmp_path / "memory.sqlite", create=True,
            )


def test_stat_module_rebinding_is_denied_before_lstat(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    def forbidden_lstat(_path: Path):
        raise AssertionError("filesystem inspected after stat module substitution")

    with monkeypatch.context() as patch:
        patch.setattr(sqlite_store, "stat", object())
        patch.setattr(Path, "lstat", forbidden_lstat)
        with pytest.raises(MemorySchemaError, match="path admission policy changed"):
            sqlite_store._require_safe_memory_path(
                tmp_path / "memory.sqlite", create=True,
            )


@pytest.mark.parametrize("name", ("S_ISDIR", "S_ISLNK", "S_ISREG", "S_IFMT"))
def test_stat_predicate_rebinding_from_lstat_callback_is_denied(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, name: str,
) -> None:
    original_lstat = Path.lstat

    def reentrant_lstat(path: Path):
        metadata = original_lstat(path)
        patch.setattr(sqlite_store.stat, name, lambda *_args: True)
        return metadata

    with monkeypatch.context() as patch:
        patch.setattr(Path, "lstat", reentrant_lstat)
        with pytest.raises(MemorySchemaError, match="path admission policy changed"):
            sqlite_store._require_safe_memory_path(
                tmp_path / "memory.sqlite", create=True,
            )


def test_stat_module_rebinding_from_lstat_callback_is_denied(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    original_lstat = Path.lstat

    def reentrant_lstat(path: Path):
        metadata = original_lstat(path)
        patch.setattr(sqlite_store, "stat", object())
        return metadata

    with monkeypatch.context() as patch:
        patch.setattr(Path, "lstat", reentrant_lstat)
        with pytest.raises(MemorySchemaError, match="path admission policy changed"):
            sqlite_store._require_safe_memory_path(
                tmp_path / "memory.sqlite", create=True,
            )


def test_stat_policy_rebinding_on_missing_leaf_is_denied(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    original_lstat = Path.lstat
    target = tmp_path / "memory.sqlite"

    def reentrant_lstat(path: Path):
        if path == target:
            patch.setattr(sqlite_store.stat, "S_ISREG", lambda *_args: True)
            raise FileNotFoundError
        return original_lstat(path)

    with monkeypatch.context() as patch:
        patch.setattr(Path, "lstat", reentrant_lstat)
        with pytest.raises(MemorySchemaError, match="path admission policy changed"):
            sqlite_store._require_safe_memory_path(target, create=True)


def test_stat_policy_rebinding_from_mode_metadata_accessor_is_denied(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    original_lstat = Path.lstat

    class ReentrantMetadata:
        @property
        def st_mode(self) -> int:
            patch.setattr(sqlite_store.stat, "S_ISDIR", lambda *_args: True)
            return stat.S_IFDIR | 0o700

        st_file_attributes = 0

    def reentrant_lstat(path: Path):
        if path == tmp_path:
            return ReentrantMetadata()
        return original_lstat(path)

    with monkeypatch.context() as patch:
        patch.setattr(Path, "lstat", reentrant_lstat)
        with pytest.raises(MemorySchemaError, match="path admission policy changed"):
            sqlite_store._require_safe_memory_path(
                tmp_path / "memory.sqlite", create=True,
            )


def test_stat_policy_rebinding_from_windows_attribute_accessor_is_denied(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    original_lstat = Path.lstat

    class ReentrantMetadata:
        st_mode = stat.S_IFDIR | 0o700

        @property
        def st_file_attributes(self) -> int:
            patch.setattr(sqlite_store.stat, "S_ISLNK", lambda *_args: True)
            return 0

    def reentrant_lstat(path: Path):
        if path == tmp_path:
            return ReentrantMetadata()
        return original_lstat(path)

    with monkeypatch.context() as patch:
        patch.setattr(Path, "lstat", reentrant_lstat)
        with pytest.raises(MemorySchemaError, match="path admission policy changed"):
            sqlite_store._require_safe_memory_path(
                tmp_path / "memory.sqlite", create=True,
            )
