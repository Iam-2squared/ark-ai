"""Run959: terminal fan-in must not resurrect dependent Planner steps.

Disconnected exact PlanGraph transitions only: no tool execution, persisted
authorization, synthetic receipt escalation, or user-PC operation.
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


def _graph() -> PlanGraph:
    ids = ("root-a", "root-b", "join", "leaf", "independent")
    dependencies = {
        "join": ("root-a", "root-b"),
        "leaf": ("join",),
    }
    return PlanGraph(tuple(
        PlanStep(
            step_id,
            ToolCall("disconnected.fixture", "offline.read", "fixture:private"),
            dependencies.get(step_id, ()),
        )
        for step_id in ids
    ))


@pytest.mark.parametrize("terminal", (StepState.FAILED, StepState.CANCELLED))
@pytest.mark.parametrize("other_first", (False, True))
def test_permuted_terminal_root_cannot_unblock_fanin_or_leaf(
    terminal: StepState, other_first: bool,
) -> None:
    graph = _graph()
    initial_topology = graph.topology_digest()
    assert {step.step_id for step in graph.ready_steps()} == {
        "root-a", "root-b", "independent",
    }
    before = graph.statuses()
    assert before["join"].state is StepState.PENDING
    assert before["join"].revision == 0

    if other_first:
        graph.transition("root-b", StepState.RUNNING, expected_revision=0)
        graph.transition("root-b", StepState.SUCCEEDED, expected_revision=1)
    graph.transition("root-a", StepState.RUNNING, expected_revision=0)
    graph.transition("root-a", terminal, expected_revision=1)
    blocked_digest = graph.status_digest()
    blocked = graph.statuses()
    for name in ("join", "leaf"):
        assert blocked[name].state is StepState.BLOCKED
        assert blocked[name].revision == 1
    assert "join" not in {step.step_id for step in graph.ready_steps()}
    assert "leaf" not in {step.step_id for step in graph.ready_steps()}

    if not other_first:
        graph.transition("root-b", StepState.RUNNING, expected_revision=0)
        graph.transition("root-b", StepState.SUCCEEDED, expected_revision=1)
    assert graph.statuses()["join"].state is StepState.BLOCKED
    assert graph.statuses()["leaf"].state is StepState.BLOCKED
    assert graph.topology_digest() == initial_topology
    assert before["join"].state is StepState.PENDING  # detached old snapshot
    assert graph.status_digest() != blocked_digest or other_first

    with pytest.raises(PlanConflictError):
        graph.transition("join", StepState.RUNNING, expected_revision=1)
    with pytest.raises(PlanConflictError):
        graph.transition("leaf", StepState.RUNNING, expected_revision=1)
    assert {step.step_id for step in graph.ready_steps()} == {"independent"}

    graph.transition("independent", StepState.RUNNING, expected_revision=0)
    graph.transition("independent", StepState.SUCCEEDED, expected_revision=1)
    assert graph.ready_steps() == ()
    assert graph.status_digest() == graph.status_digest()
    assert graph.topology_digest() == initial_topology
