"""Synthetic PlanGraph revision bounds for future durable journal compatibility."""

import pytest

from ark.agency import (
    PlanConflictError,
    PlanGraph,
    PlanStep,
    StepState,
    ToolCall,
)
from ark.agency.contracts import PlanStepStatus

_MAX = 2**63 - 1


def _plan():
    return PlanGraph((
        PlanStep("one", ToolCall("fixture.read", "fixture.read", "fixture:scope")),
    ))


def test_plan_status_accepts_exact_sqlite_max_revision():
    status = PlanStepStatus("one", StepState.PENDING, _MAX)
    assert status.revision == _MAX


@pytest.mark.parametrize("invalid", (-1, True, 0.5, _MAX + 1, 2**100))
def test_plan_status_rejects_out_of_domain_revision(invalid):
    with pytest.raises(ValueError, match="revision must be"):
        PlanStepStatus("one", StepState.PENDING, invalid)


@pytest.mark.parametrize("invalid", (True, -1, _MAX + 1, 2**100))
def test_transition_rejects_invalid_expected_revision_before_comparison(invalid):
    plan = _plan()
    with pytest.raises(ValueError, match="expected_revision"):
        plan.transition("one", StepState.RUNNING, expected_revision=invalid)
    assert plan.statuses()["one"].revision == 0


def test_transition_cannot_increment_at_sqlite_integer_limit():
    plan = _plan()
    object.__setattr__(plan._status["one"], "revision", _MAX)
    # Synthetic persisted high-revision fixture, not a runtime mutation:
    # rebaseline the private witness explicitly to test overflow preflight.
    plan._status_epoch = plan._capture_status_epoch()
    with pytest.raises(PlanConflictError, match="revision exhausted"):
        plan.transition("one", StepState.RUNNING, expected_revision=_MAX)
    assert plan.statuses()["one"].state is StepState.PENDING
    assert plan.statuses()["one"].revision == _MAX


def test_normal_plan_revision_sequence_is_unchanged():
    plan = _plan()
    first = plan.transition("one", StepState.RUNNING, expected_revision=0)
    second = plan.transition("one", StepState.SUCCEEDED, expected_revision=1)
    assert (first.revision, second.revision) == (1, 2)
