"""Memory path admission pins the stat predicates it relies on.

Synthetic in-process substitutions only; no private database or filesystem
alias is opened and no external effect is involved.
"""

from __future__ import annotations

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
