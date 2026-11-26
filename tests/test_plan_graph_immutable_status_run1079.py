"""PlanGraph status is published only as immutable revisioned snapshots."""

from types import MappingProxyType

import pytest

from ark.agency import (
    PlanConflictError,
    PlanGraph,
    PlanStep,
    StepState,
    ToolCall,
)


def _plan() -> PlanGraph:
    read = PlanStep("read", ToolCall("fixture.read", "fixture.read", "local"))
    write = PlanStep(
        "write",
        ToolCall("fixture.write", "fixture.write", "local"),
        depends_on=("read",),
    )
    return PlanGraph((read, write))


def test_status_mapping_and_epoch_fields_are_transition_managed():
    plan = _plan()
    current = plan._status["read"]

    with pytest.raises(TypeError):
        plan._status["read"] = current
    with pytest.raises(AttributeError, match="transition-managed"):
        plan._status = MappingProxyType({})
    with pytest.raises(AttributeError, match="transition-managed"):
        plan._status_mapping_epoch = plan._status
    with pytest.raises(AttributeError, match="transition-managed"):
        plan._status_epoch = ()

    assert [step.step_id for step in plan.ready_steps()] == ["read"]


def test_reflective_single_carrier_replacement_fails_closed():
    plan = _plan()
    replacement = MappingProxyType(dict(plan._status))
    object.__setattr__(plan, "_status", replacement)

    with pytest.raises(PlanConflictError, match="plan status mapping changed"):
        plan.ready_steps()


def test_reflective_status_epoch_replacement_fails_closed():
    plan = _plan()
    object.__setattr__(plan, "_status_epoch", ())

    with pytest.raises(PlanConflictError, match="plan status mapping changed"):
        plan.ready_steps()


def test_valid_transition_publishes_new_immutable_snapshot_and_cascade():
    plan = _plan()
    initial = plan._status
    running = plan.transition("read", StepState.RUNNING, expected_revision=0)

    assert plan._status is not initial
    assert type(plan._status) is MappingProxyType
    with pytest.raises(TypeError):
        plan._status["write"] = plan._status["write"]

    plan.transition("read", StepState.FAILED, expected_revision=running.revision)
    statuses = plan.statuses()
    assert statuses["read"].state is StepState.FAILED
    assert statuses["write"].state is StepState.BLOCKED


def test_replaced_assignment_guard_is_rejected_before_status_use(monkeypatch):
    plan = _plan()

    def unrestricted_setattr(instance, name, value):
        object.__setattr__(instance, name, value)

    monkeypatch.setattr(PlanGraph, "__setattr__", unrestricted_setattr)
    with pytest.raises(PlanConflictError, match="plan status mapping changed"):
        plan.ready_steps()
