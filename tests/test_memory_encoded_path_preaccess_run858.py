"""Memory SQLite fixture paths must meet encoded filesystem length budgets.

These checks are local preflight denials, not a cross-process path custody proof.
"""

from __future__ import annotations

import os
from pathlib import Path

import pytest

from ark.memory import sqlite_store as store


@pytest.mark.parametrize("absolute", (True, False))
def test_oversized_encoded_memory_path_rejected_before_lstat(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path, absolute: bool,
) -> None:
    # A Unicode path can be under the existing codepoint budget yet exceed
    # a filesystem's encoded byte budget, including -journal sidecars.
    source = (
        tmp_path / ("界" * 1400 + ".sqlite3")
        if absolute else Path("界" * 1400 + ".sqlite3")
    )
    assert len(str(source)) < 4096
    assert len(os.fsencode(source)) > 4096

    def forbid_lstat(_self: Path) -> object:
        raise AssertionError("overlong Memory path reached filesystem inventory")

    with monkeypatch.context() as patched:
        patched.setattr(Path, "lstat", forbid_lstat)
        with pytest.raises(store.MemorySchemaError, match="local fixture limits"):
            store._require_safe_memory_path(source, create=True)


def test_safe_native_memory_fixture_path_remains_admissible(tmp_path: Path) -> None:
    source = tmp_path / "memory.sqlite3"
    store._require_safe_memory_path(source, create=True)
