"""Planner journal path admission rejects Windows reparse points.

Synthetic stat metadata only: no privileged junctions or private journals.
"""

from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace

import pytest

import ark.agency.planner_journal as journal_module
from ark.agency.contracts import PlanStep, StepState, ToolCall
from ark.agency.planner import PlanGraph
from ark.agency.planner_journal import PlannerJournal, PlannerJournalPathError


def _steps() -> tuple[PlanStep, ...]:
    return (
        PlanStep(
            "root",
            ToolCall("fixture.root", "fixture.read", "synthetic:private", {"value": "root"}),
        ),
    )


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

    monkeypatch.setattr(journal_module.sqlite3, "connect", forbidden_connect)


def test_planner_rejects_reparse_point_ancestor_before_sqlite_open(
    tmp_path: Path, monkeypatch,
) -> None:
    parent = tmp_path / "nested"
    parent.mkdir()
    path = parent / "planner.sqlite3"
    _mark_reparse_point(monkeypatch, parent)
    _forbid_sqlite_open(monkeypatch)

    with pytest.raises(PlannerJournalPathError, match="ancestor refused"):
        PlannerJournal(path)


def test_planner_rejects_reparse_point_main_database_before_sqlite_open(
    tmp_path: Path, monkeypatch,
) -> None:
    path = tmp_path / "planner.sqlite3"
    journal = PlannerJournal(path)
    _mark_reparse_point(monkeypatch, path)
    _forbid_sqlite_open(monkeypatch)

    with pytest.raises(PlannerJournalPathError, match="unaliased file"):
        journal.recover("missing-plan", _steps())


def test_planner_rejects_reparse_point_sqlite_sidecar_before_sqlite_open(
    tmp_path: Path, monkeypatch,
) -> None:
    path = tmp_path / "planner.sqlite3"
    journal = PlannerJournal(path)
    sidecar = path.with_name(path.name + "-journal")
    sidecar.write_bytes(b"synthetic sidecar marker")
    _mark_reparse_point(monkeypatch, sidecar)
    _forbid_sqlite_open(monkeypatch)

    with pytest.raises(PlannerJournalPathError, match="sidecar"):
        journal.recover("missing-plan", _steps())


def test_planner_reparse_policy_rebinding_is_denied_before_lstat(
    tmp_path: Path, monkeypatch,
) -> None:
    def forbidden_lstat(_path):
        raise AssertionError("changed path policy reached filesystem")

    monkeypatch.setattr(journal_module, "_is_reparse_point", lambda _info: False)
    monkeypatch.setattr(Path, "lstat", forbidden_lstat)

    with pytest.raises(PlannerJournalPathError, match="path admission policy changed"):
        journal_module._require_safe_journal_path(
            tmp_path / "planner.sqlite3", create=True,
        )


def test_planner_reparse_attribute_requires_exact_integer() -> None:
    assert journal_module._is_reparse_point(
        SimpleNamespace(st_file_attributes=0x400)
    )
    assert not journal_module._is_reparse_point(
        SimpleNamespace(st_file_attributes=0)
    )
    assert journal_module._is_reparse_point(
        SimpleNamespace(st_file_attributes=True)
    )


def test_planner_valid_journal_still_recovers_after_unmarked_path(
    tmp_path: Path,
) -> None:
    journal = PlannerJournal(tmp_path / "planner.sqlite3")
    receipt = journal.create_plan("valid-plan", PlanGraph(_steps()))
    recovered = journal.recover("valid-plan", _steps())

    assert receipt.sequence == 0
    assert recovered.sequence == 0
    assert recovered.graph.statuses()["root"].state is StepState.PENDING
