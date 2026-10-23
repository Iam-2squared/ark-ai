"""PlanGraph detects reflected mutations of frozen plan inputs without executing tools."""

from types import MappingProxyType

import pytest

from ark.agency import PlanConflictError, PlanGraph, PlanStep, StepState, ToolCall


def _synthetic_plan() -> tuple[PlanGraph, PlanStep]:
    step = PlanStep("read", ToolCall("synthetic.read", "synthetic.read", "scope:a"))
    child = PlanStep(
        "write", ToolCall("synthetic.write", "synthetic.write", "scope:a"), ("read",)
    )
    return PlanGraph((step, child)), step


@pytest.mark.parametrize(
    "mutation",
    ["step_id", "depends_on", "call", "call_tool", "arguments", "mapping"],
)
def test_reflected_plan_inputs_are_rejected_before_transition(mutation: str) -> None:
    plan, step = _synthetic_plan()
    assert [item.step_id for item in plan.ready_steps()] == ["read"]
    if mutation == "step_id":
        object.__setattr__(step, "step_id", "changed")
    elif mutation == "depends_on":
        object.__setattr__(step, "depends_on", ("write",))
    elif mutation == "call":
        object.__setattr__(step, "call", ToolCall("different", "different", "scope:a"))
    elif mutation == "call_tool":
        object.__setattr__(step.call, "tool", "different")
    elif mutation == "arguments":
        object.__setattr__(step.call, "arguments", {"unexpected": "fixture"})
    else:
        plan.steps = MappingProxyType(dict(plan.steps))
    with pytest.raises(PlanConflictError, match="changed"):
        plan.ready_steps()
    with pytest.raises(PlanConflictError, match="changed"):
        plan.transition("read", StepState.RUNNING, expected_revision=0)
    assert plan._status["read"].revision == 0


def test_unchanged_plan_inputs_allow_revision_guarded_transitions() -> None:
    plan, _ = _synthetic_plan()
    assert [item.step_id for item in plan.ready_steps()] == ["read"]
    running = plan.transition("read", StepState.RUNNING, expected_revision=0)
    plan.transition("read", StepState.SUCCEEDED, expected_revision=running.revision)
    assert [item.step_id for item in plan.ready_steps()] == ["write"]
    assert plan.statuses()["read"].state is StepState.SUCCEEDED
