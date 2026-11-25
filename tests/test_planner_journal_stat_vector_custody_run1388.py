"""Run1388: PlannerJournal stat policy retains import-time module identity."""

from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace

import pytest

import ark.agency.planner_journal as journal_module


@pytest.mark.parametrize("stage", ("preinstalled", "lstat_callback"))
def test_joint_stat_module_and_original_alias_replacement_is_denied_before_predicate(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    stage: str,
) -> None:
    target = tmp_path / "planner.sqlite3"
    target.write_bytes(b"synthetic planner marker")
    original_lstat = Path.lstat
    predicate_calls: list[bool] = []

    def hostile_predicate(_info):
        predicate_calls.append(True)
        raise AssertionError("replacement stat predicate executed")

    fake_stat = SimpleNamespace(
        S_ISDIR=hostile_predicate,
        S_ISLNK=hostile_predicate,
        S_ISREG=hostile_predicate,
    )

    def install(patch: pytest.MonkeyPatch) -> None:
        patch.setattr(journal_module, "stat", fake_stat)
        patch.setattr(journal_module, "_ORIGINAL_STAT", fake_stat)
        patch.setattr(journal_module, "_ORIGINAL_S_ISDIR", hostile_predicate)
        patch.setattr(journal_module, "_ORIGINAL_S_ISLNK", hostile_predicate)
        patch.setattr(journal_module, "_ORIGINAL_S_ISREG", hostile_predicate)

    with monkeypatch.context() as patch:
        def lstat(path: Path):
            if stage == "preinstalled":
                raise AssertionError("preinstalled stat substitution reached lstat")
            install(patch)
            return original_lstat(path)

        if stage == "preinstalled":
            install(patch)
        patch.setattr(Path, "lstat", lstat)

        with pytest.raises(
            journal_module.PlannerJournalPathError,
            match="filesystem policy changed",
        ):
            journal_module._require_safe_journal_path(target, create=False)

    assert predicate_calls == []
    assert target.read_bytes() == b"synthetic planner marker"
