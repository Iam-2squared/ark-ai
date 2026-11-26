"""Coherent private snapshot must not follow post-init SQLite path aliases.

Only disposable fixture databases are used. No erasure, consent or external
read authorization follows from a coherent local Memory snapshot.
"""

from __future__ import annotations

import os
from pathlib import Path

import pytest

from ark.memory.coherent_snapshot_review import (
    CoherentSnapshotRequest,
    review_coherent_snapshot,
)
from ark.memory.contracts import MemorySchemaError, MemoryScope, MemoryWrite
from ark.memory.sqlite_store import SQLiteMemoryStore


def _setup(tmp_path: Path) -> tuple[SQLiteMemoryStore, Path, Path]:
    first = tmp_path / "private-owner.sqlite"
    other = tmp_path / "foreign-owner.sqlite"
    source = SQLiteMemoryStore(first, clock_ms=lambda: 100)
    foreign = SQLiteMemoryStore(other, clock_ms=lambda: 100)
    source.put(MemoryWrite(MemoryScope("owner-a", "private"), "a", "own content"))
    foreign.put(MemoryWrite(MemoryScope("owner-b", "private"), "b", "secret"))
    return source, first, other


def _review(store: SQLiteMemoryStore):
    return review_coherent_snapshot(
        store, CoherentSnapshotRequest("owner-a", ("private",)),
    )


def test_valid_private_owner_snapshot_still_reads_original_store(
    tmp_path: Path,
) -> None:
    source, path, _ = _setup(tmp_path)
    result = _review(source)
    assert path.is_file()
    assert result.records[0][0].content == "own content"
    assert result.records[0][0].scope.owner_id == "owner-a"


@pytest.mark.parametrize("alias", ("symbolic_file", "symbolic_parent", "hardlink"))
def test_postinit_alias_rejected_before_foreign_private_snapshot(
    tmp_path: Path, alias: str,
) -> None:
    source, original_path, other_path = _setup(tmp_path)
    if alias == "symbolic_file":
        redirected = tmp_path / "redirect.sqlite"
        try:
            redirected.symlink_to(other_path)
        except (OSError, NotImplementedError):
            pytest.skip("local symlinks unavailable")
    elif alias == "symbolic_parent":
        alias_parent = tmp_path / "aliased"
        target_parent = tmp_path / "true-parent"
        target_parent.mkdir()
        moved = target_parent / "moved.sqlite"
        os.link(other_path, moved)
        # Avoid using a hardlinked fixture as the only evidence of this
        # parent alias: the parent symlink should be denied first.
        try:
            alias_parent.symlink_to(target_parent, target_is_directory=True)
        except (OSError, NotImplementedError):
            pytest.skip("local directory symlinks unavailable")
        redirected = alias_parent / "moved.sqlite"
    else:
        redirected = tmp_path / "redirect.sqlite"
        try:
            os.link(other_path, redirected)
        except OSError:
            pytest.skip("hardlinks unavailable")
    source.path = redirected
    with pytest.raises(MemorySchemaError, match="symbolic|single regular"):
        _review(source)
    assert original_path.is_file()
    assert other_path.is_file()


def test_postinit_aliased_sqlite_sidecar_is_denied(
    tmp_path: Path,
) -> None:
    source, original_path, _ = _setup(tmp_path)
    sidecar = Path(str(original_path) + "-journal")
    try:
        sidecar.symlink_to(tmp_path / "nonexistent-sidecar")
    except (OSError, NotImplementedError):
        pytest.skip("symlinks unavailable")
    with pytest.raises(MemorySchemaError, match="sidecar"):
        _review(source)
    assert original_path.is_file()
