"""Run947: two independent failure waves cannot re-open quarantined DAG work.

This is an in-memory, disconnected Planner fixture; no tool backend runs.
"""

from __future__ import annotations

import pytest

from ark.agency import (
    PlanConflictError,
    PlanGraph,
    PlanStep,
    StepState,
    ToolCall,
)


def _plan() -> PlanGraph:
    inert = ToolCall("synthetic.read", "synthetic.read", "local-only")
    return PlanGraph((
        PlanStep("first", inert),
        PlanStep("first-child", inert, ("first",)),
        PlanStep("first-grandchild", inert, ("first-child",)),
        PlanStep("other", inert),
        PlanStep("other-child", inert, ("other",)),
        PlanStep("join", inert, ("first-grandchild", "other")),
    ))


def _finish(graph: PlanGraph, name: str, terminal: StepState) -> None:
    if terminal is StepState.BLOCKED:
        graph.transition(name, StepState.BLOCKED, expected_revision=0)
    else:
        running = graph.transition(name, StepState.RUNNING, expected_revision=0)
        graph.transition(name, terminal, expected_revision=running.revision)


@pytest.mark.parametrize("first_terminal", (
    StepState.FAILED, StepState.CANCELLED, StepState.BLOCKED,
))
@pytest.mark.parametrize("other_terminal", (
    StepState.FAILED, StepState.CANCELLED, StepState.BLOCKED,
))
def test_two_terminal_waves_never_republish_or_unlock_blocked_join(
    first_terminal: StepState, other_terminal: StepState,
) -> None:
    graph = _plan()
    original_topology = graph.topology_digest()
    _finish(graph, "first", first_terminal)
    first_wave = graph.statuses()
    assert first_wave["join"].state is StepState.BLOCKED
    assert first_wave["join"].revision == 1
    assert first_wave["other"].state is StepState.PENDING
    assert first_wave["other-child"].state is StepState.PENDING
    assert {step.step_id for step in graph.ready_steps()} == {"other"}

    _finish(graph, "other", other_terminal)
    after = graph.statuses()
    assert after["first"].state is first_terminal
    assert after["other"].state is other_terminal
    for dependent in ("first-child", "first-grandchild", "other-child", "join"):
        assert after[dependent].state is StepState.BLOCKED
        assert after[dependent].revision == 1
    assert graph.ready_steps() == ()
    assert graph.topology_digest() == original_topology

    terminal_digest = graph.status_digest()
    with pytest.raises(PlanConflictError):
        graph.transition("join", StepState.RUNNING, expected_revision=1)
    with pytest.raises(PlanConflictError):
        graph.transition("first-child", StepState.RUNNING, expected_revision=0)
    assert graph.status_digest() == terminal_digest
    assert graph.statuses()["join"].revision == 1
