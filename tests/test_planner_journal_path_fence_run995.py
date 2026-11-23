"""Run995: Planner journal path custody and no-recreation regressions."""

from __future__ import annotations

import os
from pathlib import Path

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


def _link(source: Path, target: Path, *, directory: bool = False) -> None:
    try:
        target.symlink_to(source, target_is_directory=directory)
    except (OSError, NotImplementedError) as exc:
        pytest.skip(f"filesystem symlinks are unavailable: {exc}")


def test_valid_existing_parent_and_relative_path_remain_usable(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.chdir(tmp_path)
    journal = PlannerJournal(Path("planner.sqlite3"))
    graph = PlanGraph(_steps())
    receipt = journal.create_plan("relative-plan", graph)
    recovered = journal.recover("relative-plan", _steps())

    assert receipt.sequence == 0
    assert recovered.sequence == 0
    assert recovered.graph.statuses()["root"].state is StepState.PENDING


def test_missing_parent_is_rejected_without_creating_directories(tmp_path: Path) -> None:
    parent = tmp_path / "missing" / "nested"
    with pytest.raises(PlannerJournalPathError, match="parent directory"):
        PlannerJournal(parent / "planner.sqlite3")
    assert not parent.exists()


def test_parent_symlink_is_rejected_before_sqlite_open(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    real = tmp_path / "real"
    real.mkdir()
    linked = tmp_path / "linked"
    _link(real, linked, directory=True)

    def forbidden_connect(*_args, **_kwargs):
        raise AssertionError("unsafe parent must be rejected before sqlite3.connect")

    monkeypatch.setattr(journal_module.sqlite3, "connect", forbidden_connect)
    with pytest.raises(PlannerJournalPathError, match="ancestor"):
        PlannerJournal(linked / "planner.sqlite3")
    assert not (real / "planner.sqlite3").exists()


def test_leaf_symlink_is_rejected_before_sqlite_open(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    target = tmp_path / "target.sqlite3"
    PlannerJournal(target)
    before = target.read_bytes()
    alias = tmp_path / "alias.sqlite3"
    _link(target, alias)

    def forbidden_connect(*_args, **_kwargs):
        raise AssertionError("symlink leaf must be rejected before sqlite3.connect")

    monkeypatch.setattr(journal_module.sqlite3, "connect", forbidden_connect)
    with pytest.raises(PlannerJournalPathError, match="unaliased file"):
        PlannerJournal(alias)
    assert target.read_bytes() == before


def test_leaf_alias_swapped_after_startup_is_rejected_on_reopen(tmp_path: Path) -> None:
    path = tmp_path / "planner.sqlite3"
    journal = PlannerJournal(path)
    held = tmp_path / "held.sqlite3"
    path.rename(held)
    _link(held, path)

    with pytest.raises(PlannerJournalPathError, match="unaliased file"):
        journal.recover("missing-plan", _steps())
    assert held.exists()


def test_missing_database_after_startup_is_not_silently_recreated(tmp_path: Path) -> None:
    path = tmp_path / "planner.sqlite3"
    journal = PlannerJournal(path)
    path.rename(tmp_path / "retained.sqlite3")

    with pytest.raises(PlannerJournalPathError, match="recreation is refused"):
        journal.recover("missing-plan", _steps())
    assert not path.exists()


def test_hardlinked_database_is_rejected_on_reopen(tmp_path: Path) -> None:
    path = tmp_path / "planner.sqlite3"
    journal = PlannerJournal(path)
    alias = tmp_path / "alias.sqlite3"
    try:
        os.link(path, alias)
    except OSError as exc:
        pytest.skip(f"hard links are unavailable: {exc}")

    with pytest.raises(PlannerJournalPathError, match="unaliased file"):
        journal.recover("missing-plan", _steps())


def test_orphaned_sqlite_sidecar_is_not_adopted(tmp_path: Path) -> None:
    path = tmp_path / "planner.sqlite3"
    sidecar = tmp_path / "planner.sqlite3-wal"
    sidecar.write_bytes(b"synthetic orphan sidecar")

    with pytest.raises(PlannerJournalPathError, match="orphaned"):
        PlannerJournal(path)
    assert not path.exists()
    assert sidecar.read_bytes() == b"synthetic orphan sidecar"


def test_symlinked_sqlite_sidecar_is_rejected_on_reopen(tmp_path: Path) -> None:
    path = tmp_path / "planner.sqlite3"
    journal = PlannerJournal(path)
    target = tmp_path / "outside.bin"
    target.write_bytes(b"synthetic sidecar target")
    sidecar = tmp_path / "planner.sqlite3-wal"
    _link(target, sidecar)

    with pytest.raises(PlannerJournalPathError, match="sidecar"):
        journal.recover("missing-plan", _steps())
    assert target.read_bytes() == b"synthetic sidecar target"


@pytest.mark.parametrize("kind", ["database-directory", "parent-is-file"])
def test_nonregular_database_or_parent_is_rejected(tmp_path: Path, kind: str) -> None:
    if kind == "database-directory":
        target = tmp_path / "planner.sqlite3"
        target.mkdir()
    else:
        parent = tmp_path / "parent-file"
        parent.write_text("fixture", encoding="utf-8")
        target = parent / "planner.sqlite3"

    with pytest.raises(PlannerJournalPathError):
        PlannerJournal(target)


def test_lexical_parent_traversal_is_rejected_before_io(tmp_path: Path) -> None:
    target = tmp_path / "nested" / ".." / "planner.sqlite3"
    with pytest.raises(PlannerJournalPathError, match="traversal"):
        PlannerJournal(target)
    assert not (tmp_path / "planner.sqlite3").exists()
