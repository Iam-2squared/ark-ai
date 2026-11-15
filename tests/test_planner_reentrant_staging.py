"""Non-UI regression: valid reentrant transitions must not lose newer status."""

import pytest

import ark.agency.planner as planner_module
from ark.agency import PlanConflictError, PlanGraph, PlanStep, StepState, ToolCall


def _graph(*, cascading: bool = False) -> PlanGraph:
    call = ToolCall("fixture.read", "fixture.read", "synthetic")
    steps = [
        PlanStep("alpha", call),
        PlanStep("other", call),
    ]
    if cascading:
        steps.extend(
            [
                PlanStep("dependent", call, ("alpha",)),
                PlanStep("grandchild", call, ("dependent",)),
            ]
        )
    return PlanGraph(tuple(steps))


@pytest.mark.parametrize("same_step", [False, True])
def test_reentrant_status_advance_does_not_get_overwritten(
    monkeypatch: pytest.MonkeyPatch, same_step: bool,
) -> None:
    graph = _graph()
    original_replace = planner_module.replace
    invoked = False

    def reentrant_replace(value: object, **changes: object) -> object:
        nonlocal invoked
        if not invoked and changes.get("state") is StepState.RUNNING:
            invoked = True
            if same_step:
                graph.transition("alpha", StepState.CANCELLED, expected_revision=0)
            else:
                graph.transition("other", StepState.RUNNING, expected_revision=0)
        return original_replace(value, **changes)

    monkeypatch.setattr(planner_module, "replace", reentrant_replace)
    with pytest.raises(
        PlanConflictError, match="status advanced during transition staging",
    ):
        graph.transition("alpha", StepState.RUNNING, expected_revision=0)

    assert invoked
    states = graph.statuses()
    assert states["alpha"].state is (
        StepState.CANCELLED if same_step else StepState.PENDING
    )
    assert states["alpha"].revision == (1 if same_step else 0)
    assert states["other"].state is (
        StepState.PENDING if same_step else StepState.RUNNING
    )
    assert states["other"].revision == (0 if same_step else 1)


def test_reentrant_transition_cannot_publish_partial_terminal_cascade(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    graph = _graph(cascading=True)
    graph.transition("alpha", StepState.RUNNING, expected_revision=0)
    original_replace = planner_module.replace
    invoked = False

    def reentrant_replace(value: object, **changes: object) -> object:
        nonlocal invoked
        if not invoked and changes.get("state") is StepState.BLOCKED:
            invoked = True
            graph.transition("other", StepState.RUNNING, expected_revision=0)
        return original_replace(value, **changes)

    monkeypatch.setattr(planner_module, "replace", reentrant_replace)
    with pytest.raises(
        PlanConflictError, match="status advanced during transition staging",
    ):
        graph.transition("alpha", StepState.FAILED, expected_revision=1)

    assert invoked
    states = graph.statuses()
    assert states["alpha"].state is StepState.RUNNING
    assert states["alpha"].revision == 1
    assert states["dependent"].state is StepState.PENDING
    assert states["grandchild"].state is StepState.PENDING
    assert states["other"].state is StepState.RUNNING
    assert states["other"].revision == 1
