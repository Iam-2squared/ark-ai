"""A Planner must not accept new equal-valued ToolCall/PlanStep carriers.

This is in-memory exact-input validation, not persisted authorization,
registry binding, clock attestation or real backend execution.
"""

import pytest

from ark.agency import (
    PlanConflictError,
    PlanGraph,
    PlanStep,
    StepState,
    ToolCall,
)


@pytest.mark.parametrize("field", ["tool", "capability", "scope", "step_id"])
def test_reflected_equal_text_replacement_is_not_original_plan_input(field):
    call = ToolCall(
        "fixture.tool.read.506",
        "fixture.capability.read.506",
        "fixture.scope.506",
        {"key": "value"},
    )
    step = PlanStep("fixture.step.506", call)
    plan = PlanGraph((step,))
    assert plan.ready_steps() == (step,)
    target = step if field == "step_id" else call
    original = getattr(target, field)
    replacement = ("_" + original)[1:]
    assert replacement == original and replacement is not original
    object.__setattr__(target, field, replacement)

    with pytest.raises(PlanConflictError, match="plan step input changed"):
        plan.ready_steps()
    with pytest.raises(PlanConflictError, match="plan step input changed"):
        plan.topology_digest()
    with pytest.raises(PlanConflictError, match="plan step input changed"):
        plan.transition("fixture.step.506", StepState.RUNNING, expected_revision=0)
    assert plan._status["fixture.step.506"].state is StepState.PENDING
    assert plan._status["fixture.step.506"].revision == 0


def test_unchanged_original_step_still_transitions_deterministically():
    call = ToolCall("fixture.tool.read.506", "fixture.capability.read.506", "scope")
    step = PlanStep("fixture.step.506", call)
    plan = PlanGraph((step,))
    assert plan.ready_steps() == (step,)
    running = plan.transition(step.step_id, StepState.RUNNING, expected_revision=0)
    assert running.state is StepState.RUNNING
    finished = plan.transition(step.step_id, StepState.SUCCEEDED, expected_revision=1)
    assert finished.state is StepState.SUCCEEDED
    assert plan.ready_steps() == ()
