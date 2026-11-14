"""Regression: planner internal status cannot be forged between transitions."""

import pytest

from ark.agency.contracts import (
    PlanConflictError,
    PlanStep,
    PlanStepStatus,
    StepState,
    ToolCall,
)
from ark.agency.planner import PlanGraph


def _plan() -> PlanGraph:
    root = PlanStep("root", ToolCall("fixture.read", "read", "synthetic"))
    child = PlanStep(
        "child", ToolCall("fixture.write", "write", "synthetic"), ("root",)
    )
    return PlanGraph((root, child))


@pytest.mark.parametrize("mutation", [
    "state", "revision", "step_id", "replace", "replace_map",
    "remove", "add", "bool_revision",
])
def test_reflected_or_replaced_private_status_denied(mutation: str) -> None:
    graph = _plan()
    carrier = graph._status["root"]
    if mutation == "state":
        object.__setattr__(carrier, "state", StepState.SUCCEEDED)
    elif mutation == "revision":
        object.__setattr__(carrier, "revision", 1)
    elif mutation == "step_id":
        object.__setattr__(carrier, "step_id", "child")
    elif mutation == "replace":
        graph._status["root"] = PlanStepStatus("root", StepState.PENDING)
    elif mutation == "replace_map":
        graph._status = dict(graph._status)
    elif mutation == "remove":
        del graph._status["root"]
    elif mutation == "add":
        graph._status["unknown"] = PlanStepStatus("unknown", StepState.PENDING)
    else:
        object.__setattr__(carrier, "revision", True)

    with pytest.raises(PlanConflictError, match="status"):
        graph.ready_steps()
    with pytest.raises(PlanConflictError, match="status"):
        graph.statuses()
    with pytest.raises(PlanConflictError, match="status"):
        graph.status_digest()
    with pytest.raises(PlanConflictError, match="status"):
        graph.transition("root", StepState.RUNNING, expected_revision=0)


def test_valid_cascade_updates_status_epoch_atomically() -> None:
    graph = _plan()
    running = graph.transition("root", StepState.RUNNING, expected_revision=0)
    assert graph.statuses()["root"] == running
    graph.transition("root", StepState.FAILED, expected_revision=1)
    assert graph.statuses()["child"].state is StepState.BLOCKED
    assert graph.statuses()["child"].revision == 1
    assert graph.ready_steps() == ()
    assert graph.status_digest().startswith("pstate_")


def test_failed_transition_does_not_advance_authoritative_epoch() -> None:
    graph = _plan()
    before = graph.status_digest()
    with pytest.raises(PlanConflictError, match="dependencies"):
        graph.transition("child", StepState.RUNNING, expected_revision=0)
    assert graph.status_digest() == before
    assert tuple(step.step_id for step in graph.ready_steps()) == ("root",)


def test_returned_status_is_detached_and_cannot_spoof_internal_epoch() -> None:
    graph = _plan()
    detached = graph.statuses()["root"]
    object.__setattr__(detached, "state", StepState.SUCCEEDED)
    graph.transition("root", StepState.RUNNING, expected_revision=0)
    assert graph.statuses()["root"].state is StepState.RUNNING
