"""Planner ready-step snapshots reject a legitimate reentrant transition.

Synthetic local DAG only: no tool dispatch, real-world action or UI coupling.
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
    return PlanGraph(
        (
            PlanStep("root", ToolCall("fixture", "read", "local")),
            PlanStep(
                "dependent", ToolCall("fixture", "read", "local"),
                depends_on=("root",),
            ),
        )
    )


@pytest.mark.parametrize("injection_phase", ("preflight", "postscan"))
def test_reentrant_transition_during_readiness_never_returns_stale_steps(
    monkeypatch: pytest.MonkeyPatch, injection_phase: str,
) -> None:
    graph = _graph()
    assert tuple(step.step_id for step in graph.ready_steps()) == ("root",)
    original = PlanGraph._assert_plan_epoch
    calls = 0
    fired = False
    target = 1 if injection_phase == "preflight" else 2

    def reentrant(self: PlanGraph) -> None:
        nonlocal calls, fired
        original(self)
        if self is graph and not fired:
            calls += 1
            if calls == target:
                fired = True
                # The transition itself is valid. The *older* runnable list
                # becomes stale even though the graph remains internally sound.
                graph.transition("root", StepState.RUNNING, expected_revision=0)

    with monkeypatch.context() as patch:
        patch.setattr(PlanGraph, "_assert_plan_epoch", reentrant)
        with pytest.raises(PlanConflictError, match="readiness"):
            graph.ready_steps()
    assert fired
    assert graph.statuses()["root"].state is StepState.RUNNING
    assert graph.ready_steps() == ()


def test_stable_readiness_and_terminal_propagation_unchanged() -> None:
    graph = _graph()
    assert tuple(step.step_id for step in graph.ready_steps()) == ("root",)
    graph.transition("root", StepState.RUNNING, expected_revision=0)
    assert graph.ready_steps() == ()
    graph.transition("root", StepState.FAILED, expected_revision=1)
    assert graph.statuses()["dependent"].state is StepState.BLOCKED
    assert graph.ready_steps() == ()
