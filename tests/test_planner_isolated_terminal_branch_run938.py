"""A terminal Planner branch must not consume an independent runnable branch.

These are disconnected in-process DAG transitions. They deliberately do not
call any tool, reconstruct unproven external results or grant retry authority.
"""

from __future__ import annotations

import pytest

from ark.agency.contracts import (
    PlanConflictError,
    PlanStep,
    StepState,
    ToolCall,
)
from ark.agency.planner import PlanGraph


def _step(name: str, *parents: str) -> PlanStep:
    return PlanStep(
        name,
        ToolCall("fixture.read", "fixture.read", "fixture:owner", {"step": name}),
        depends_on=parents,
    )


@pytest.mark.parametrize("terminal", (StepState.FAILED, StepState.CANCELLED))
def test_terminal_cascade_preserves_isolated_ready_branch(
    terminal: StepState,
) -> None:
    plan = PlanGraph((
        _step("root"),
        _step("child", "root"),
        _step("grandchild", "child"),
        _step("independent"),
        _step("independent-child", "independent"),
    ))
    initial_topology = plan.topology_digest()
    assert {step.step_id for step in plan.ready_steps()} == {
        "root", "independent",
    }

    plan.transition("root", StepState.RUNNING, expected_revision=0)
    plan.transition("root", terminal, expected_revision=1)
    states = plan.statuses()
    assert (states["root"].state, states["root"].revision) == (terminal, 2)
    for name in ("child", "grandchild"):
        assert (states[name].state, states[name].revision) == (
            StepState.BLOCKED, 1,
        )
    assert (states["independent"].state, states["independent"].revision) == (
        StepState.PENDING, 0,
    )
    assert plan.topology_digest() == initial_topology
    assert tuple(step.step_id for step in plan.ready_steps()) == ("independent",)

    # A stale completion or blocked-child retry must not mutate any branch.
    before = plan.status_digest()
    with pytest.raises(PlanConflictError):
        plan.transition("root", StepState.SUCCEEDED, expected_revision=1)
    with pytest.raises(PlanConflictError):
        plan.transition("child", StepState.RUNNING, expected_revision=1)
    assert plan.status_digest() == before

    # An unrelated synthetic branch can still progress using its own CAS.
    plan.transition("independent", StepState.RUNNING, expected_revision=0)
    plan.transition("independent", StepState.SUCCEEDED, expected_revision=1)
    assert tuple(step.step_id for step in plan.ready_steps()) == (
        "independent-child",
    )
    assert plan.statuses()["grandchild"].state is StepState.BLOCKED
    assert plan.topology_digest() == initial_topology
