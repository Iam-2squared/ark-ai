"""Post-publication reentry must not return an obsolete Planner receipt.

Synthetic in-memory DAG only. A final-copy callback may advance status even
though every live status and its epoch remain internally consistent. Rejection
never rolls back either in-memory transition or authorizes execution/replay.
"""

import pytest

import ark.agency.planner as planner_module
from ark.agency import PlanConflictError, PlanGraph, PlanStep, StepState, ToolCall


def _graph() -> PlanGraph:
    call = ToolCall("fixture.read", "fixture.read", "synthetic")
    return PlanGraph((
        PlanStep("alpha", call),
        PlanStep("dependent", call, ("alpha",)),
        PlanStep("other", call),
    ))


@pytest.mark.parametrize("same_step", [False, True])
def test_final_copy_nested_transition_refuses_obsolete_receipt(
    monkeypatch: pytest.MonkeyPatch, same_step: bool,
) -> None:
    graph = _graph()
    original_replace = planner_module.replace
    called = False

    def reentrant_copy(value: object, **changes: object) -> object:
        nonlocal called
        if (
            not called
            and not changes
            and value.step_id == "alpha"
            and value.state is StepState.RUNNING
        ):
            called = True
            if same_step:
                graph.transition("alpha", StepState.SUCCEEDED, expected_revision=1)
            else:
                graph.transition("other", StepState.RUNNING, expected_revision=0)
        return original_replace(value, **changes)

    with monkeypatch.context() as patch:
        patch.setattr(planner_module, "replace", reentrant_copy)
        with pytest.raises(
            PlanConflictError,
            match="status advanced during final transition snapshot",
        ):
            graph.transition("alpha", StepState.RUNNING, expected_revision=0)

    assert called
    statuses = graph.statuses()
    if same_step:
        assert (statuses["alpha"].state, statuses["alpha"].revision) == (
            StepState.SUCCEEDED, 2,
        )
        assert statuses["other"].state is StepState.PENDING
    else:
        assert (statuses["alpha"].state, statuses["alpha"].revision) == (
            StepState.RUNNING, 1,
        )
        assert (statuses["other"].state, statuses["other"].revision) == (
            StepState.RUNNING, 1,
        )
    assert statuses["dependent"].state is StepState.PENDING


def test_final_copy_nested_independent_transition_preserves_terminal_cascade(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    graph = _graph()
    graph.transition("alpha", StepState.RUNNING, expected_revision=0)
    original_replace = planner_module.replace
    called = False

    def reentrant_copy(value: object, **changes: object) -> object:
        nonlocal called
        if (
            not called
            and not changes
            and value.step_id == "alpha"
            and value.state is StepState.FAILED
        ):
            called = True
            graph.transition("other", StepState.RUNNING, expected_revision=0)
        return original_replace(value, **changes)

    with monkeypatch.context() as patch:
        patch.setattr(planner_module, "replace", reentrant_copy)
        with pytest.raises(
            PlanConflictError,
            match="status advanced during final transition snapshot",
        ):
            graph.transition("alpha", StepState.FAILED, expected_revision=1)

    assert called
    statuses = graph.statuses()
    assert (statuses["alpha"].state, statuses["alpha"].revision) == (
        StepState.FAILED, 2,
    )
    assert (statuses["dependent"].state, statuses["dependent"].revision) == (
        StepState.BLOCKED, 1,
    )
    assert (statuses["other"].state, statuses["other"].revision) == (
        StepState.RUNNING, 1,
    )


def test_uninterrupted_transition_still_returns_current_detached_receipt() -> None:
    graph = _graph()
    receipt = graph.transition("alpha", StepState.RUNNING, expected_revision=0)
    status = graph.statuses()["alpha"]
    assert receipt is not graph._status["alpha"]
    assert receipt.state is status.state is StepState.RUNNING
    assert receipt.revision == status.revision == 1
