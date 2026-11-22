"""Planner journal path admission pins the stat predicates it relies on.

Synthetic in-process substitutions only; no journal or external effect is opened.
"""

from __future__ import annotations

from pathlib import Path

import pytest

import ark.agency.planner_journal_review as journal


@pytest.mark.parametrize("name", ("S_ISDIR", "S_ISLNK", "S_ISREG"))
def test_stat_predicate_rebinding_is_denied_before_lstat(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, name: str,
) -> None:
    def forbidden_lstat(_path: Path):
        raise AssertionError("filesystem inspected after stat predicate substitution")

    with monkeypatch.context() as patch:
        patch.setattr(journal.stat, name, lambda *_args: True)
        patch.setattr(Path, "lstat", forbidden_lstat)
        with pytest.raises(
            journal.SyntheticPlanJournalRejected,
            match="reparse-point policy changed",
        ):
            journal._require_safe_journal_path(tmp_path / "plan.sqlite")


def test_stat_module_rebinding_is_denied_before_lstat(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    def forbidden_lstat(_path: Path):
        raise AssertionError("filesystem inspected after stat module substitution")

    with monkeypatch.context() as patch:
        patch.setattr(journal, "stat", object())
        patch.setattr(Path, "lstat", forbidden_lstat)
        with pytest.raises(
            journal.SyntheticPlanJournalRejected,
            match="reparse-point policy changed",
        ):
            journal._require_safe_journal_path(tmp_path / "plan.sqlite")
