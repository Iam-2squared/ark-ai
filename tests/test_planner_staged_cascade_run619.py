"""Staged terminal cascades cannot publish partial statuses on constructor failure."""

import pytest

import ark.agency.planner as planner
from ark.agency import PlanGraph, PlanStep, StepState, ToolCall
from ark.agency.contracts import PlanConflictError, PlanStepStatus


def _graph():
    call = ToolCall("fixture.read", "fixture.read", "local")
    return PlanGraph((
        PlanStep("root", call),
        PlanStep("first", call, ("root",)),
        PlanStep("second", call, ("root",)),
        PlanStep("grandchild", call, ("second",)),
        PlanStep("independent", call),
    ))


@pytest.mark.parametrize("fail_at", (1, 2, 3, 4))
def test_replace_failure_before_publish_does_not_mutate_any_plan_state(
    monkeypatch, fail_at,
):
    graph = _graph()
    before = dict(graph.statuses())
    digest = graph.status_digest()
    original = planner.replace
    calls = []

    def fail_at_stage(value, **updates):
        calls.append(value.step_id)
        if len(calls) == fail_at:
            raise RuntimeError("synthetic stage interruption")
        return original(value, **updates)

    with monkeypatch.context() as patch:
        patch.setattr(planner, "replace", fail_at_stage)
        with pytest.raises(RuntimeError, match="stage interruption"):
            graph.transition("root", StepState.BLOCKED, expected_revision=0)

    assert len(calls) == fail_at
    assert dict(graph.statuses()) == before
    assert graph.status_digest() == digest
    assert tuple(step.step_id for step in graph.ready_steps()) == (
        "independent", "root",
    )


def test_noncanonical_staged_status_is_rejected_without_publishing(monkeypatch):
    graph = _graph()
    original = planner.replace
    before = dict(graph.statuses())

    def forge_stage(value, **updates):
        if value.step_id == "first":
            return PlanStepStatus("first", StepState.SUCCEEDED, 1)
        return original(value, **updates)

    with monkeypatch.context() as patch:
        patch.setattr(planner, "replace", forge_stage)
        with pytest.raises(PlanConflictError, match="staged"):
            graph.transition("root", StepState.BLOCKED, expected_revision=0)

    assert dict(graph.statuses()) == before


def test_complete_cascade_still_has_expected_revisions_and_independent_ready():
    graph = _graph()
    graph.transition("root", StepState.BLOCKED, expected_revision=0)
    snapshot = graph.statuses()
    for name in ("root", "first", "second", "grandchild"):
        assert snapshot[name].state is StepState.BLOCKED
        assert snapshot[name].revision == 1
    assert snapshot["independent"].state is StepState.PENDING
    assert tuple(step.step_id for step in graph.ready_steps()) == ("independent",)
