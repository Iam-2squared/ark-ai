"""Synthetic path admission and post-open cleanup tests for occurrence storage."""

from __future__ import annotations

import sqlite3
from pathlib import Path
from types import SimpleNamespace

import pytest

import ark.agency.durable_occurrence_review as occurrence_module
from ark.agency.durable_occurrence_review import (
    SyntheticOccurrenceStore,
    SyntheticReplayRejected,
)


def _store(tmp_path: Path) -> SyntheticOccurrenceStore:
    return SyntheticOccurrenceStore(tmp_path / "occurrences.sqlite")


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


def _reparse_after_open(monkeypatch, target: Path):
    original_lstat = Path.lstat
    state = {"opened": False}

    def marked_lstat(path):
        info = original_lstat(path)
        if state["opened"] and path == target:
            return SimpleNamespace(
                st_mode=info.st_mode,
                st_nlink=info.st_nlink,
                st_file_attributes=0x400,
            )
        return info

    monkeypatch.setattr(Path, "lstat", marked_lstat)
    original_connect = occurrence_module.sqlite3.connect
    opened = []

    def connect(*args, **kwargs):
        connection = original_connect(*args, **kwargs)
        opened.append(connection)
        state["opened"] = True
        return connection

    monkeypatch.setattr(occurrence_module.sqlite3, "connect", connect)
    return opened


def _assert_closed(connection: sqlite3.Connection) -> None:
    with pytest.raises(sqlite3.ProgrammingError, match="closed"):
        connection.execute("SELECT 1")


@pytest.mark.parametrize("location", ["ancestor", "main", "sidecar"])
def test_occurrence_ledger_rejects_reparse_paths_before_sqlite_open(
    tmp_path: Path, monkeypatch, location: str,
) -> None:
    store = _store(tmp_path)
    if location == "ancestor":
        target = tmp_path
    elif location == "main":
        target = store._path
    else:
        target = store._path.with_name(store._path.name + "-wal")
        target.write_bytes(b"synthetic sidecar")

    _mark_reparse_point(monkeypatch, target)

    def forbidden_connect(*_args, **_kwargs):
        raise AssertionError("reparse-point occurrence path reached SQLite")

    monkeypatch.setattr(occurrence_module.sqlite3, "connect", forbidden_connect)
    with pytest.raises(SyntheticReplayRejected, match="reparse|sidecar alias"):
        store._connect()


def test_occurrence_reparse_attribute_requires_exact_integer() -> None:
    assert occurrence_module._is_reparse_point(
        SimpleNamespace(st_file_attributes=0x400)
    )
    assert not occurrence_module._is_reparse_point(
        SimpleNamespace(st_file_attributes=0)
    )
    assert occurrence_module._is_reparse_point(
        SimpleNamespace(st_file_attributes=True)
    )


@pytest.mark.parametrize("mode", ["write", "read"])
def test_occurrence_ledger_rechecks_path_after_open_and_closes_handle(
    tmp_path: Path, monkeypatch, mode: str,
) -> None:
    store = _store(tmp_path)
    opened = _reparse_after_open(monkeypatch, store._path)

    with pytest.raises(SyntheticReplayRejected, match="reparse"):
        if mode == "write":
            store._connect()
        else:
            store.count_synthetic()

    assert len(opened) == 1
    _assert_closed(opened[0])


def test_occurrence_constructor_rechecks_path_after_create_and_closes_handle(
    tmp_path: Path, monkeypatch,
) -> None:
    path = tmp_path / "new-occurrences.sqlite"
    opened = _reparse_after_open(monkeypatch, path)

    with pytest.raises(SyntheticReplayRejected, match="reparse"):
        SyntheticOccurrenceStore(path)

    assert len(opened) == 1
    _assert_closed(opened[0])
