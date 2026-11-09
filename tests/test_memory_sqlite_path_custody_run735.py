"""Synthetic local Memory path alias controls; no user data or external effects."""

from __future__ import annotations

import os
import sqlite3
from pathlib import Path

import pytest

from ark.memory.contracts import MemorySchemaError, MemoryScope, MemoryWrite
from ark.memory.sqlite_store import SQLiteMemoryStore


def _store(path: Path | str) -> SQLiteMemoryStore:
    return SQLiteMemoryStore(path, clock_ms=lambda: 1_000)


def _link(source: Path, target: Path, *, is_directory: bool = False) -> None:
    try:
        target.symlink_to(source, target_is_directory=is_directory)
    except (OSError, NotImplementedError) as exc:
        pytest.skip(f"symlinks unsupported in fixture environment: {exc}")


def test_valid_nested_sqlite_memory_path_remains_usable(tmp_path: Path) -> None:
    store = _store(tmp_path / "nested" / "memory.sqlite")
    scope = MemoryScope("synthetic-owner")
    record = store.put(MemoryWrite(scope, "synthetic-source", "inert text"))
    assert record.revision == 1
    assert [(event.operation, event.event_id) for event in store.events(scope)] == [
        ("create", 1)
    ]


def test_valid_relative_sqlite_memory_path_still_supported(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.chdir(tmp_path)
    store = _store("nested/local.sqlite")
    assert store.path == Path("nested/local.sqlite")
    assert store.events(MemoryScope("synthetic-owner")) == []


def test_symbolic_ancestor_refused_before_bootstrap(tmp_path: Path) -> None:
    real = tmp_path / "real"
    real.mkdir()
    linked = tmp_path / "linked"
    _link(real, linked, is_directory=True)
    with pytest.raises(MemorySchemaError):
        _store(linked / "secret.sqlite")
    assert not (real / "secret.sqlite").exists()


def test_symbolic_leaf_refused_before_bootstrap(tmp_path: Path) -> None:
    existing = tmp_path / "existing.sqlite"
    _store(existing)
    linked = tmp_path / "linked.sqlite"
    _link(existing, linked)
    with pytest.raises(MemorySchemaError):
        _store(linked)


def test_symbolic_leaf_swapped_after_startup_refused_on_read(
    tmp_path: Path,
) -> None:
    db = tmp_path / "memory.sqlite"
    store = _store(db)
    retained = tmp_path / "retained.sqlite"
    db.rename(retained)
    _link(retained, db)
    with pytest.raises(MemorySchemaError):
        store.events(MemoryScope("synthetic-owner"))


def test_symbolic_leaf_swapped_after_startup_refused_on_write(
    tmp_path: Path,
) -> None:
    db = tmp_path / "memory.sqlite"
    store = _store(db)
    retained = tmp_path / "retained.sqlite"
    db.rename(retained)
    _link(retained, db)
    with pytest.raises(MemorySchemaError):
        store.put(
            MemoryWrite(MemoryScope("synthetic-owner"), "synthetic", "inert text")
        )


def test_hardlinked_database_refused_on_reopen(tmp_path: Path) -> None:
    db = tmp_path / "memory.sqlite"
    store = _store(db)
    alias = tmp_path / "alias.sqlite"
    try:
        os.link(db, alias)
    except OSError as exc:
        pytest.skip(f"hardlinks unsupported in fixture environment: {exc}")
    with pytest.raises(MemorySchemaError):
        store.events(MemoryScope("synthetic-owner"))


@pytest.mark.parametrize("kind", ["directory", "nondirectory-parent"])
def test_nonregular_or_nondirectory_sqlite_path_refused(
    tmp_path: Path, kind: str
) -> None:
    if kind == "directory":
        target = tmp_path / "is-a-directory"
        target.mkdir()
    else:
        parent = tmp_path / "parent-is-file"
        parent.write_text("fixture", encoding="utf-8")
        target = parent / "memory.sqlite"
    with pytest.raises(MemorySchemaError):
        _store(target)


def test_lexical_parent_traversal_refused_before_directory_creation(
    tmp_path: Path,
) -> None:
    with pytest.raises(MemorySchemaError):
        _store(tmp_path / "nested" / ".." / "escaped.sqlite")
    assert not (tmp_path / "escaped.sqlite").exists()


def test_untrusted_pathlike_callback_is_never_executed() -> None:
    touched: list[str] = []

    class HostilePath:
        def __fspath__(self) -> str:
            touched.append("called")
            return "hidden-private-path.sqlite"

    with pytest.raises(MemorySchemaError):
        _store(HostilePath())  # type: ignore[arg-type]
    assert touched == []


def test_missing_database_after_startup_cannot_be_recreated(tmp_path: Path) -> None:
    db = tmp_path / "memory.sqlite"
    store = _store(db)
    db.rename(tmp_path / "held.sqlite")
    with pytest.raises(sqlite3.OperationalError):
        store.events(MemoryScope("synthetic-owner"))
    assert not db.exists()
