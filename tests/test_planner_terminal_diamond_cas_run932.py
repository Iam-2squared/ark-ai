"""Planner terminal diamonds: CAS transitions never awaken blocked descendants.

This is an in-memory, disconnected state-machine regression, not proof that
a recovered external WRITE completed or may be retried.
"""

from __future__ import annotations

import pytest

from ark.agency import PlanConflictError, PlanGraph, PlanStep, StepState, ToolCall

CALL = ToolCall("local.fixture", "private.test", "scope:fixture", {"x": 1})


def _plan() -> PlanGraph:
    # a -> (b,c) -> d, plus an unrelated e -> f branch.
    return PlanGraph((
        PlanStep("a", CALL),
        PlanStep("b", CALL, ("a",)),
        PlanStep("c", CALL, ("a",)),
        PlanStep("d", CALL, ("b", "c")),
        PlanStep("e", CALL),
        PlanStep("f", CALL, ("e",)),
    ))


@pytest.mark.parametrize(
    "terminal",
    (StepState.FAILED, StepState.CANCELLED, StepState.BLOCKED),
)
def test_terminal_root_blocks_both_diamond_sides_and_join_once(
    terminal: StepState,
) -> None:
    plan = _plan()
    assert tuple(x.step_id for x in plan.ready_steps()) == ("a", "e")
    if terminal in (StepState.FAILED, StepState.CANCELLED):
        running = plan.transition("a", StepState.RUNNING, expected_revision=0)
        terminal_revision = running.revision
    else:
        terminal_revision = 0
    result = plan.transition("a", terminal, expected_revision=terminal_revision)
    assert result.revision == terminal_revision + 1
    statuses = plan.statuses()
    assert statuses["a"].state is terminal
    assert tuple(statuses[key].state for key in ("b", "c", "d")) == (
        StepState.BLOCKED, StepState.BLOCKED, StepState.BLOCKED,
    )
    assert tuple(statuses[key].revision for key in ("b", "c", "d")) == (1, 1, 1)
    assert statuses["e"].revision == statuses["f"].revision == 0
    assert tuple(x.step_id for x in plan.ready_steps()) == ("e",)

    # The blocked join is neither implicitly runnable nor a valid retry.
    for key in ("b", "c", "d"):
        with pytest.raises(PlanConflictError):
            plan.transition(key, StepState.RUNNING, expected_revision=1)
    assert tuple(plan.statuses()[key].revision for key in ("b", "c", "d")) == (
        1, 1, 1,
    )


@pytest.mark.parametrize("invalid_revision", (-1, True, 2**63))
def test_invalid_cas_does_not_partially_publish_diamond(
    invalid_revision: object,
) -> None:
    plan = _plan()
    before = plan.statuses()
    with pytest.raises((ValueError, PlanConflictError)):
        plan.transition("a", StepState.BLOCKED, expected_revision=invalid_revision)
    assert plan.statuses() == before
    assert tuple(step.step_id for step in plan.ready_steps()) == ("a", "e")


def test_independent_branch_can_finish_without_replaying_terminal_root() -> None:
    plan = _plan()
    first = plan.transition("a", StepState.RUNNING, expected_revision=0)
    plan.transition("a", StepState.FAILED, expected_revision=first.revision)
    other = plan.transition("e", StepState.RUNNING, expected_revision=0)
    plan.transition("e", StepState.SUCCEEDED, expected_revision=other.revision)
    assert tuple(x.step_id for x in plan.ready_steps()) == ("f",)
    with pytest.raises(PlanConflictError, match="invalid transition"):
        plan.transition("a", StepState.RUNNING, expected_revision=2)
    before = plan.statuses()
    with pytest.raises(PlanConflictError, match="revision mismatch"):
        plan.transition("f", StepState.RUNNING, expected_revision=1)
    assert plan.statuses() == before
    assert plan.transition("f", StepState.RUNNING, expected_revision=0).state is (
        StepState.RUNNING
    )
