"""Mock-only Planner terminal DAG recovery is persistent, never a retry signal.

Failures propagate through pending descendants without fabricating journal
events for each derived BLOCKED state. RUNNING after restart is ambiguous.
"""

from __future__ import annotations

import pytest

from ark.agency.contracts import (
    PlanConflictError,
    PlanStep,
    StepState,
    ToolCall,
)
from ark.agency.planner_journal_review import SyntheticPlanJournal

A, B, C, D = ("step_" + letter * 16 for letter in "abcd")


def _journal(tmp_path):
    steps = (
        PlanStep(A, ToolCall("math.sum", "math.sum", "private", {"values": [1]})),
        PlanStep(B, ToolCall("math.sum", "math.sum", "private", {"values": [2]}), (A,)),
        PlanStep(C, ToolCall("math.sum", "math.sum", "private", {"values": [3]}), (A,)),
        PlanStep(D, ToolCall("math.sum", "math.sum", "private", {"values": [4]}), (B, C)),
    )
    path = tmp_path / "planner-terminal.sqlite"
    journal = SyntheticPlanJournal(path, steps)
    genesis = journal.recover().tail
    return path, steps, journal, genesis


def _finish(journal, genesis, step_id, tick, *, success=True):
    journal.append(
        step_id, StepState.RUNNING,
        expected_revision=0, at_ms=tick, retained=genesis,
    )
    return journal.append(
        step_id, StepState.SUCCEEDED if success else StepState.FAILED,
        expected_revision=1, at_ms=tick + 1, retained=genesis,
    )


@pytest.mark.parametrize(
    ("failed", "preceding", "blocked", "pending", "count"),
    (
        (A, (), (B, C, D), (), 2),
        (B, (A,), (D,), (C,), 4),
        (C, (A, B), (D,), (), 6),
    ),
)
def test_failed_branch_retains_exact_derived_blocked_states_after_restart(
    tmp_path, failed, preceding, blocked, pending, count,
):
    path, steps, journal, genesis = _journal(tmp_path)
    tick = 1
    for name in preceding:
        _finish(journal, genesis, name, tick)
        tick += 2
    recorded = _finish(journal, genesis, failed, tick, success=False)
    assert recorded.tail.event_count == count
    reopened = SyntheticPlanJournal(path, steps).recover(retained=genesis)
    assert reopened == recorded
    statuses = {
        name: (state, revision)
        for name, state, revision in reopened.step_statuses
    }
    assert statuses[failed] == ("failed", 2)
    for name in preceding:
        assert statuses[name] == ("succeeded", 2)
    for name in blocked:
        assert statuses[name] == ("blocked", 1)
    for name in pending:
        assert statuses[name] == ("pending", 0)
    assert reopened.ambiguous_running_steps == ()
    assert reopened.dispatch_authorized is False
    assert reopened.automatic_replay_authorized is False


def test_running_leaf_after_restart_is_ambiguous_and_cannot_repeat_running(tmp_path):
    path, steps, journal, genesis = _journal(tmp_path)
    for i, name in enumerate((A, B, C)):
        _finish(journal, genesis, name, 2 * i + 1)
    running = journal.append(
        D, StepState.RUNNING,
        expected_revision=0, at_ms=7, retained=genesis,
    )
    reopened = SyntheticPlanJournal(path, steps).recover(retained=genesis)
    assert reopened == running
    assert reopened.ambiguous_running_steps == (D,)
    assert dict((name, state) for name, state, _ in reopened.step_statuses)[D] == "running"
    assert reopened.dispatch_authorized is False
    assert reopened.automatic_replay_authorized is False
    with pytest.raises(PlanConflictError, match="invalid transition"):
        SyntheticPlanJournal(path, steps).append(
            D, StepState.RUNNING,
            expected_revision=1, at_ms=8, retained=genesis,
        )
    assert SyntheticPlanJournal(path, steps).recover(retained=genesis) == reopened
