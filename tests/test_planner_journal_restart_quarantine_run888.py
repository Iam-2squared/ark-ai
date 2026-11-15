"""Crash/restart quarantine for disconnected Planner journal transitions.

No ToolBackend dispatch, automatic retry, human approval or protected
evaluation. This suite only uses a temporary synthetic SQLite journal.
"""

from dataclasses import replace

import pytest

from ark.agency.contracts import (
    PlanConflictError, PlanStep, StepState, ToolCall,
)
from ark.agency.planner_journal_review import (
    SyntheticPlanJournal, SyntheticPlanJournalRejected,
)


def _steps() -> tuple[PlanStep, ...]:
    call = ToolCall("offline.inspect", "fixture.read", "synthetic", {})
    return (
        PlanStep("alpha", call),
        PlanStep("beta", call, ("alpha",)),
        PlanStep("gamma", call, ("beta",)),
    )


def test_restart_retains_running_as_ambiguous_never_dispatches(tmp_path):
    path = tmp_path / "plan.db"
    initial = SyntheticPlanJournal(path, _steps())
    genesis = initial.recover()
    first = initial.append(
        "alpha", StepState.RUNNING, expected_revision=0,
        at_ms=100, retained=genesis.tail,
    )
    restarted = SyntheticPlanJournal(path, _steps())
    recovered = restarted.recover(retained=genesis.tail)
    assert recovered.tail == first.tail
    assert ("alpha", "running", 1) in recovered.step_statuses
    assert recovered.ambiguous_running_steps == ("alpha",)
    assert recovered.dispatch_authorized is False
    assert recovered.automatic_replay_authorized is False


def test_restart_does_not_replay_ambiguous_running_transition(tmp_path):
    path = tmp_path / "plan.db"
    journal = SyntheticPlanJournal(path, _steps())
    first = journal.append(
        "alpha", StepState.RUNNING, expected_revision=0, at_ms=100,
    )
    after_restart = SyntheticPlanJournal(path, _steps())
    with pytest.raises((PlanConflictError, SyntheticPlanJournalRejected)):
        after_restart.append(
            "alpha", StepState.RUNNING, expected_revision=0,
            at_ms=101, retained=first.tail,
        )
    recovered = after_restart.recover(retained=first.tail)
    assert recovered.tail == first.tail
    assert recovered.ambiguous_running_steps == ("alpha",)


def test_terminal_failure_cascades_to_all_pending_descendants_on_recovery(tmp_path):
    path = tmp_path / "plan.db"
    journal = SyntheticPlanJournal(path, _steps())
    journal.append("alpha", StepState.RUNNING, expected_revision=0, at_ms=1)
    terminal = journal.append(
        "alpha", StepState.FAILED, expected_revision=1, at_ms=2,
    )
    recovered = SyntheticPlanJournal(path, _steps()).recover()
    assert recovered.tail == terminal.tail
    assert recovered.step_statuses == (
        ("alpha", "failed", 2),
        ("beta", "blocked", 1),
        ("gamma", "blocked", 1),
    )
    assert recovered.ambiguous_running_steps == ()
    assert recovered.automatic_replay_authorized is False


def test_clock_regression_keeps_existing_journal_tail(tmp_path):
    path = tmp_path / "plan.db"
    journal = SyntheticPlanJournal(path, _steps())
    first = journal.append(
        "alpha", StepState.RUNNING, expected_revision=0, at_ms=200,
    )
    with pytest.raises(SyntheticPlanJournalRejected, match="clock regression"):
        journal.append(
            "alpha", StepState.SUCCEEDED, expected_revision=1,
            at_ms=199, retained=first.tail,
        )
    assert journal.recover().tail == first.tail


def test_external_retained_prefix_mismatch_is_rejected_without_transition(tmp_path):
    path = tmp_path / "plan.db"
    journal = SyntheticPlanJournal(path, _steps())
    genesis = journal.recover()
    forged = replace(genesis.tail, event_hash="pevt_" + "0" * 64)
    with pytest.raises(SyntheticPlanJournalRejected):
        journal.append(
            "alpha", StepState.RUNNING, expected_revision=0,
            at_ms=1, retained=forged,
        )
    assert journal.recover().tail == genesis.tail


def test_reopening_with_different_plan_topology_is_rejected(tmp_path):
    path = tmp_path / "plan.db"
    journal = SyntheticPlanJournal(path, _steps())
    original = journal.recover().tail
    changed = _steps()[:-1]
    with pytest.raises(SyntheticPlanJournalRejected):
        SyntheticPlanJournal(path, changed)
    assert SyntheticPlanJournal(path, _steps()).recover().tail == original
