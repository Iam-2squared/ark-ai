"""Planner journal append must never recreate an initialized missing ledger."""

import sqlite3

import pytest

from ark.agency.contracts import PlanStep, StepState, ToolCall
from ark.agency.planner_journal_review import SyntheticPlanJournal


def _steps():
    return (PlanStep("root", ToolCall(
        "fixture", "offline", "disconnected", {"private": "do-not-output"},
    )),)


@pytest.mark.parametrize("missing", ["moved", "deleted"])
def test_append_fails_closed_without_creating_missing_journal(tmp_path, missing):
    path = tmp_path / "plan # percent %.sqlite"
    journal = SyntheticPlanJournal(path, _steps())
    known = journal.append("root", StepState.RUNNING, expected_revision=0, at_ms=10)
    if missing == "moved":
        safe_copy = tmp_path / "moved.sqlite"
        path.rename(safe_copy)
    else:
        path.unlink()
    with pytest.raises(sqlite3.OperationalError):
        journal.append("root", StepState.SUCCEEDED, expected_revision=1, at_ms=11)
    assert not path.exists()
    if missing == "moved":
        recovered = SyntheticPlanJournal(safe_copy, _steps()).recover(retained=known.tail)
        assert recovered.ambiguous_running_steps == ("root",)
        assert recovered.automatic_replay_authorized is False


def test_cold_journal_creation_still_requires_explicit_constructor(tmp_path):
    path = tmp_path / "plan # percent %.sqlite"
    assert not path.exists()
    journal = SyntheticPlanJournal(path, _steps())
    assert path.exists()
    result = journal.append("root", StepState.RUNNING, expected_revision=0, at_ms=10)
    assert result.ambiguous_running_steps == ("root",)
    assert result.dispatch_authorized is False
    assert result.automatic_replay_authorized is False


def test_append_preserves_cas_on_existing_uri_special_path(tmp_path):
    path = tmp_path / "plan # percent %.sqlite"
    journal = SyntheticPlanJournal(path, _steps())
    first = journal.append("root", StepState.RUNNING, expected_revision=0, at_ms=10)
    assert first.tail.event_count == 1
    with pytest.raises(RuntimeError):
        journal.append("root", StepState.RUNNING, expected_revision=0, at_ms=11)
    assert journal.recover() == first


def test_restored_original_database_can_be_recovered_but_not_autoreplayed(tmp_path):
    path = tmp_path / "plan # percent %.sqlite"
    journal = SyntheticPlanJournal(path, _steps())
    first = journal.append("root", StepState.RUNNING, expected_revision=0, at_ms=10)
    moved = tmp_path / "moved.sqlite"
    path.rename(moved)
    with pytest.raises(sqlite3.OperationalError):
        journal.recover()
    moved.rename(path)
    assert journal.recover(retained=first.tail).ambiguous_running_steps == ("root",)
    assert journal.recover().automatic_replay_authorized is False
