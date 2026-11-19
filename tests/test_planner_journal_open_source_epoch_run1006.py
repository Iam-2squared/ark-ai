"""Planner journal open pins its source path and forbids raced recreation."""

from __future__ import annotations

import sqlite3
from pathlib import Path

import pytest

import ark.agency.planner_journal as journal_module
from ark.agency.planner_journal import (
    PlannerJournal,
    PlannerJournalPathError,
)


def _journal(path: Path) -> PlannerJournal:
    return PlannerJournal(path)


def test_planner_journal_rejects_source_rebind_after_open_and_closes_handle(
    tmp_path: Path, monkeypatch,
) -> None:
    journal = _journal(tmp_path / "primary.sqlite")
    replacement = _journal(tmp_path / "replacement.sqlite")
    original_connect = journal_module.sqlite3.connect
    opened = []

    def rebind_after_open(*args, **kwargs):
        connection = original_connect(*args, **kwargs)
        opened.append(connection)
        journal._path = str(replacement._path)
        return connection

    monkeypatch.setattr(journal_module.sqlite3, "connect", rebind_after_open)
    with pytest.raises(PlannerJournalPathError, match="source changed during"):
        journal._connect()

    assert len(opened) == 1
    with pytest.raises(sqlite3.ProgrammingError, match="closed"):
        opened[0].execute("SELECT 1")


def test_planner_journal_noncreate_open_does_not_recreate_after_preflight(
    tmp_path: Path, monkeypatch,
) -> None:
    path = tmp_path / "planner.sqlite"
    journal = _journal(path)
    expected_uri = path.as_uri() + "?mode=rw"
    original_connect = journal_module.sqlite3.connect
    removed = []

    def remove_after_preflight(database, *args, **kwargs):
        if database == expected_uri:
            path.unlink()
            removed.append(True)
        return original_connect(database, *args, **kwargs)

    monkeypatch.setattr(
        journal_module.sqlite3, "connect", remove_after_preflight,
    )
    with pytest.raises(sqlite3.OperationalError):
        journal._connect()

    assert removed == [True]
    assert not path.exists()
