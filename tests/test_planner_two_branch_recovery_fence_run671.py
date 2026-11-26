"""Planner restart keeps uncertain, terminal, and independent WRITE lanes apart.

All statuses are local journal fixtures. Fence codes never authorize dispatch,
external observations, tool access, retry, or a durable approval grant.
"""

from __future__ import annotations

import pytest

from ark.agency.contracts import PlanStep, StepState, ToolCall
from ark.agency.disconnected_planner_fence_projection import (
    DisconnectedPlannerProjectionRejected,
    project_disconnected_planner_fence,
)
from ark.agency.planner_journal_review import SyntheticPlanJournal

_ROOT_A = "step_" + "a" * 16
_CHILD_A = "step_" + "b" * 16
_LEAF_A = "step_" + "c" * 16
_ROOT_B = "step_" + "d" * 16
_CHILD_B = "step_" + "e" * 16
_FREE_WRITE = "step_" + "f" * 16


def _fixture(tmp_path):
    steps = (
        PlanStep(_ROOT_A, ToolCall("offline", "read", "local", {"n": 1})),
        PlanStep(
            _CHILD_A, ToolCall("offline", "write", "local", {"n": 2}),
            (_ROOT_A,),
        ),
        PlanStep(
            _LEAF_A, ToolCall("offline", "read", "local", {"n": 3}),
            (_CHILD_A,),
        ),
        PlanStep(_ROOT_B, ToolCall("offline", "read", "local", {"n": 4})),
        PlanStep(
            _CHILD_B, ToolCall("offline", "write", "local", {"n": 5}),
            (_ROOT_B,),
        ),
        PlanStep(
            _FREE_WRITE, ToolCall("offline", "write", "local", {"n": 6}),
        ),
    )
    effects = (
        (_ROOT_A, "READ"), (_CHILD_A, "WRITE"), (_LEAF_A, "READ"),
        (_ROOT_B, "READ"), (_CHILD_B, "WRITE"), (_FREE_WRITE, "WRITE"),
    )
    journal = SyntheticPlanJournal(tmp_path / "six-step-restart.sqlite", steps)
    return journal, steps, effects


@pytest.mark.parametrize("terminal", (StepState.FAILED, StepState.CANCELLED))
@pytest.mark.parametrize("free_write_started", (False, True))
def test_recovered_branches_keep_terminal_uncertain_and_write_hold_isolated(
    tmp_path, terminal, free_write_started,
):
    journal, steps, effects = _fixture(tmp_path)
    initial = journal.recover()
    journal.append(
        _ROOT_A, StepState.RUNNING,
        expected_revision=0, at_ms=100, retained=initial.tail,
    )
    journal.append(
        _ROOT_B, StepState.RUNNING,
        expected_revision=0, at_ms=101, retained=initial.tail,
    )
    journal.append(
        _ROOT_B, terminal,
        expected_revision=1, at_ms=102, retained=initial.tail,
    )
    if free_write_started:
        journal.append(
            _FREE_WRITE, StepState.RUNNING,
            expected_revision=0, at_ms=103, retained=initial.tail,
        )
    restarted = SyntheticPlanJournal(journal._path, steps)
    recovered = restarted.recover(retained=initial.tail)
    before = restarted.recover()
    fence = project_disconnected_planner_fence(recovered, steps, effects)
    codes = {item.step_id: item.code for item in fence.decisions}
    assert codes == {
        _ROOT_A: "QUARANTINE_UNKNOWN",
        _CHILD_A: "HOLD_UNCERTAIN",
        _LEAF_A: "HOLD_UNCERTAIN",
        _ROOT_B: "TERMINAL",
        _CHILD_B: "TERMINAL",
        _FREE_WRITE: (
            "QUARANTINE_WRITE_UNKNOWN"
            if free_write_started else "HELD_WRITE_APPROVAL"
        ),
    }
    assert fence.dispatch_authorized is False
    assert fence.automatic_replay_authorized is False
    assert fence.write_authorized is False
    assert fence.external_outcome_verified is False
    assert restarted.recover() == before


def test_forged_cancellation_cannot_rewrite_recovered_status_digest(tmp_path):
    journal, steps, effects = _fixture(tmp_path)
    authentic = journal.recover()
    forged = journal.recover()
    object.__setattr__(
        forged, "step_statuses",
        tuple(
            (name, "cancelled" if name == _ROOT_A else status, revision)
            for name, status, revision in forged.step_statuses
        ),
    )
    with pytest.raises(
        DisconnectedPlannerProjectionRejected, match="statuses differ",
    ):
        project_disconnected_planner_fence(forged, steps, effects)
    assert journal.recover() == authentic
