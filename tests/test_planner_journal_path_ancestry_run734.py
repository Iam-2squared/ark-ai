"""Planner journal path custody: local-only, non-dispatching SQLite fixtures.

Symbolic parent redirects and lexical escapes must not create or re-open
another database. Local lstat checks are not atomic directory-fd provenance.
"""

from __future__ import annotations

import os
from pathlib import Path

import pytest

from ark.agency.contracts import PlanStep, StepState, ToolCall
from ark.agency.planner_journal_review import (
    SyntheticPlanJournal,
    SyntheticPlanJournalRejected,
)

STEPS = (
    PlanStep("root", ToolCall("fixture", "offline", "local", {"n": 1})),
)


def test_nested_absolute_path_remains_recoverable(tmp_path: Path):
    target = tmp_path / "real" / "deep" / "plan.sqlite"
    target.parent.mkdir(parents=True)
    journal = SyntheticPlanJournal(target, STEPS)
    witness = journal.append("root", StepState.RUNNING, expected_revision=0, at_ms=1)
    recovered = SyntheticPlanJournal(target, STEPS).recover(retained=witness.tail)
    assert recovered.ambiguous_running_steps == ("root",)
    assert recovered.automatic_replay_authorized is False
    assert recovered.dispatch_authorized is False


def test_symlinked_grandparent_refused_before_sqlite_open(tmp_path: Path):
    real = tmp_path / "real"
    deep = real / "deep"
    deep.mkdir(parents=True)
    original = deep / "original.sqlite"
    SyntheticPlanJournal(original, STEPS)
    before = original.read_bytes()

    alias = tmp_path / "alias"
    try:
        alias.symlink_to(real, target_is_directory=True)
    except (OSError, NotImplementedError) as exc:
        pytest.skip(f"directory symlinks unavailable: {exc}")
    with pytest.raises(SyntheticPlanJournalRejected, match="ancestor"):
        SyntheticPlanJournal(alias / "deep" / "other.sqlite", STEPS)
    assert not (deep / "other.sqlite").exists()
    with pytest.raises(SyntheticPlanJournalRejected, match="ancestor"):
        SyntheticPlanJournal(alias / "deep" / "original.sqlite", STEPS)
    assert original.read_bytes() == before


@pytest.mark.parametrize("operation", ("create", "recover"))
def test_parent_traversal_is_refused(tmp_path: Path, operation: str):
    (tmp_path / "real").mkdir()
    target = tmp_path / "real" / ".." / "escaping.sqlite"
    with pytest.raises(SyntheticPlanJournalRejected, match="absolute non-traversing"):
        if operation == "create":
            SyntheticPlanJournal(target, STEPS)
        else:
            # Recover from a carrier whose original Path is lexically unsafe
            # cannot be used to mint a fresh file in another parent.
            SyntheticPlanJournal(target, STEPS).recover()
    assert not (tmp_path / "escaping.sqlite").exists()


def test_relative_path_rejected_before_db_creation():
    with pytest.raises(SyntheticPlanJournalRejected, match="absolute non-traversing"):
        SyntheticPlanJournal(Path("untrusted-relative-plan.sqlite"), STEPS)


def test_file_as_parent_does_not_create_sqlite(tmp_path: Path):
    blocker = tmp_path / "blocker"
    blocker.write_bytes(b"not a directory")
    with pytest.raises(SyntheticPlanJournalRejected, match="ancestor"):
        SyntheticPlanJournal(blocker / "plan.sqlite", STEPS)
    assert blocker.read_bytes() == b"not a directory"


def test_directory_as_journal_refused_before_db_open(tmp_path: Path):
    directory = tmp_path / "plan.sqlite"
    directory.mkdir()
    with pytest.raises(SyntheticPlanJournalRejected, match="one regular file"):
        SyntheticPlanJournal(directory, STEPS)


def test_hardlinked_journal_refused_before_db_open(tmp_path: Path):
    original = tmp_path / "original.sqlite"
    SyntheticPlanJournal(original, STEPS)
    alias = tmp_path / "alias.sqlite"
    try:
        os.link(original, alias)
    except (OSError, NotImplementedError) as exc:
        pytest.skip(f"hardlinks unavailable: {exc}")
    with pytest.raises(SyntheticPlanJournalRejected, match="one regular file"):
        SyntheticPlanJournal(alias, STEPS)
    with pytest.raises(SyntheticPlanJournalRejected, match="one regular file"):
        SyntheticPlanJournal(original, STEPS)
