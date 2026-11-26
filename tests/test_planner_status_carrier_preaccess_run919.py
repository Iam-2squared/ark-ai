"""Planner status integrity refuses reflected foreign labels before equality.

Disconnected synthetic DAG only. No tool execution, approval or durable
recovery authority is inferred from local status witnesses.
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


class _ForbiddenEquality:
    def __eq__(self, _other):
        raise AssertionError("foreign equality must not be called")

    def __ne__(self, _other):
        raise AssertionError("foreign inequality must not be called")


def _graph():
    return PlanGraph((
        PlanStep("root", ToolCall("fixture.read", "fixture.read", "sandbox")),
    ))


@pytest.mark.parametrize("carrier", (_ForbiddenEquality(), True, None, 123))
@pytest.mark.parametrize("operation", ("statuses", "status_digest", "ready", "transition"))
def test_reflected_status_step_label_rejected_without_foreign_comparison(
    carrier, operation,
):
    graph = _graph()
    object.__setattr__(graph._status["root"], "step_id", carrier)
    with pytest.raises(PlanConflictError, match="plan status identity"):
        if operation == "statuses":
            graph.statuses()
        elif operation == "status_digest":
            graph.status_digest()
        elif operation == "ready":
            graph.ready_steps()
        else:
            graph.transition("root", StepState.RUNNING, expected_revision=0)


def test_detached_status_mutation_does_not_change_graph_or_topology():
    graph = _graph()
    topology_before = graph.topology_digest()
    status_before = graph.status_digest()
    detached = graph.statuses()
    object.__setattr__(detached["root"], "step_id", "untrusted-copy")
    assert graph.statuses()["root"].step_id == "root"
    assert graph.topology_digest() == topology_before
    running = graph.transition("root", StepState.RUNNING, expected_revision=0)
    assert running.state is StepState.RUNNING
    assert graph.status_digest() != status_before
    assert graph.topology_digest() == topology_before
