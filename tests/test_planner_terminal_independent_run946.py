"""Run946: terminal dependency propagation does not block unrelated DAG lanes.

Planner state is deterministic in-memory topology, never external execution.
"""

from __future__ import annotations

import pytest

from ark.agency import PlanGraph, PlanStep, StepState, ToolCall


def _graph() -> PlanGraph:
    call = ToolCall("synthetic.read", "synthetic.read", "local-only")
    return PlanGraph((
        PlanStep("a-root", call),
        PlanStep("b-child", call, ("a-root",)),
        PlanStep("c-grandchild", call, ("b-child",)),
        PlanStep("d-independent", call),
        PlanStep("e-fan-in", call, ("c-grandchild", "d-independent")),
        PlanStep("f-independent-child", call, ("d-independent",)),
    ))


@pytest.mark.parametrize("terminal", (
    StepState.FAILED, StepState.CANCELLED, StepState.BLOCKED,
))
def test_terminal_root_quarantines_only_descendants(
    terminal: StepState,
) -> None:
    graph = _graph()
    initial_topology = graph.topology_digest()
    initial_status = graph.status_digest()
    if terminal is StepState.BLOCKED:
        graph.transition("a-root", terminal, expected_revision=0)
    else:
        running = graph.transition(
            "a-root", StepState.RUNNING, expected_revision=0,
        )
        graph.transition(
            "a-root", terminal, expected_revision=running.revision,
        )
    statuses = graph.statuses()
    assert statuses["a-root"].state is terminal
    for dependent in ("b-child", "c-grandchild", "e-fan-in"):
        assert statuses[dependent].state is StepState.BLOCKED
    assert statuses["d-independent"].state is StepState.PENDING
    assert statuses["f-independent-child"].state is StepState.PENDING
    assert {step.step_id for step in graph.ready_steps()} == {"d-independent"}

    independent = graph.transition(
        "d-independent", StepState.RUNNING, expected_revision=0,
    )
    graph.transition(
        "d-independent", StepState.SUCCEEDED,
        expected_revision=independent.revision,
    )
    states = graph.statuses()
    assert states["e-fan-in"].state is StepState.BLOCKED
    assert states["f-independent-child"].state is StepState.PENDING
    assert {step.step_id for step in graph.ready_steps()} == {
        "f-independent-child",
    }
    assert graph.topology_digest() == initial_topology
    assert graph.status_digest() != initial_status
