"""Replayed Planner witnesses pin durable prefixes, not dispatch authority.

All tests use temporary synthetic SQLite stores; no action executor or user data.
"""

import pytest

from ark.agency.contracts import PlanConflictError, PlanStep, StepState, ToolCall
from ark.agency.planner_journal_review import (
    SyntheticPlanJournal,
    SyntheticPlanJournalRejected,
)


def _steps() -> tuple[PlanStep, ...]:
    call = ToolCall("offline.inspect", "fixture.read", "synthetic", {})
    return (
        PlanStep("first", call),
        PlanStep("second", call, ("first",)),
        PlanStep("third", call, ("second",)),
    )


def test_original_retained_genesis_is_valid_after_multiple_commits(tmp_path):
    path = tmp_path / "journal.sqlite"
    journal = SyntheticPlanJournal(path, _steps())
    independent_genesis = journal.recover().tail
    running = journal.append(
        "first", StepState.RUNNING, expected_revision=0,
        at_ms=10, retained=independent_genesis,
    )
    finished = journal.append(
        "first", StepState.SUCCEEDED, expected_revision=1,
        at_ms=11, retained=independent_genesis,
    )
    restarted = SyntheticPlanJournal(path, _steps())
    recovery = restarted.recover(retained=independent_genesis)
    assert recovery.tail == finished.tail
    assert recovery.tail.event_count == 2
    assert recovery.tail != running.tail
    assert recovery.step_statuses == (
        ("first", "succeeded", 2), ("second", "pending", 0),
        ("third", "pending", 0),
    )
    assert recovery.dispatch_authorized is False
    assert recovery.automatic_replay_authorized is False


def test_diverged_independent_tail_cannot_be_accepted_as_prefix(tmp_path):
    path_a = tmp_path / "a.sqlite"
    path_b = tmp_path / "b.sqlite"
    a = SyntheticPlanJournal(path_a, _steps())
    b = SyntheticPlanJournal(path_b, _steps())
    old_a = a.append(
        "first", StepState.RUNNING, expected_revision=0, at_ms=10,
    ).tail
    b.append("first", StepState.RUNNING, expected_revision=0, at_ms=20)
    unchanged = b.recover().tail
    assert old_a.event_hash != unchanged.event_hash
    with pytest.raises(SyntheticPlanJournalRejected, match="history changed"):
        b.recover(retained=old_a)
    with pytest.raises(SyntheticPlanJournalRejected, match="history changed"):
        b.append(
            "first", StepState.FAILED, expected_revision=1,
            at_ms=21, retained=old_a,
        )
    assert b.recover().tail == unchanged


def test_middle_running_remains_unknown_after_restart_and_stale_cas(tmp_path):
    path = tmp_path / "journal.sqlite"
    journal = SyntheticPlanJournal(path, _steps())
    journal.append("first", StepState.RUNNING, expected_revision=0, at_ms=10)
    journal.append("first", StepState.SUCCEEDED, expected_revision=1, at_ms=11)
    running = journal.append("second", StepState.RUNNING, expected_revision=0, at_ms=12)
    reopened = SyntheticPlanJournal(path, _steps())
    recovery = reopened.recover()
    assert recovery.tail == running.tail
    assert recovery.ambiguous_running_steps == ("second",)
    assert recovery.step_statuses == (
        ("first", "succeeded", 2), ("second", "running", 1),
        ("third", "pending", 0),
    )
    assert recovery.automatic_replay_authorized is False
    with pytest.raises((PlanConflictError, SyntheticPlanJournalRejected)):
        reopened.append(
            "second", StepState.RUNNING, expected_revision=0, at_ms=13,
            retained=running.tail,
        )
    assert reopened.recover().tail == running.tail
