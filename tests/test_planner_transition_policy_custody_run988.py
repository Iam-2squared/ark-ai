"""Planner terminal transitions cannot be expanded through module policy rebinding."""

from types import MappingProxyType

import pytest

from ark.agency import PlanConflictError, PlanGraph, PlanStep, StepState, ToolCall
from ark.agency import planner


def _steps():
    return (
        PlanStep("root", ToolCall("mock.read", "mock.read", "local:fixtures")),
        PlanStep(
            "leaf",
            ToolCall("mock.read", "mock.read", "local:fixtures"),
            depends_on=("root",),
        ),
    )


def _replace_policy(monkeypatch, tamper):
    if tamper in ("same_contents", "direct_success", "terminal_restart"):
        values = dict(planner._ALLOWED)
        if tamper == "direct_success":
            values[StepState.PENDING] = frozenset({StepState.SUCCEEDED})
        elif tamper == "terminal_restart":
            values[StepState.SUCCEEDED] = frozenset({StepState.RUNNING})
        monkeypatch.setattr(planner, "_ALLOWED", MappingProxyType(values))
    elif tamper == "ordinary_dict":
        monkeypatch.setattr(planner, "_ALLOWED", dict(planner._ALLOWED))
    elif tamper == "rows_baseline":
        monkeypatch.setattr(planner, "_ORIGINAL_ALLOWED_ROWS", ())
    elif tamper == "original_binding":
        monkeypatch.setattr(
            planner, "_ORIGINAL_ALLOWED_POLICY",
            MappingProxyType(dict(planner._ALLOWED)),
        )


@pytest.mark.parametrize(
    "tamper",
    [
        "same_contents",
        "direct_success",
        "terminal_restart",
        "ordinary_dict",
        "rows_baseline",
        "original_binding",
    ],
)
@pytest.mark.parametrize("operation", ["construct", "ready", "statuses", "transition"])
def test_plan_rejects_modified_transition_policy_without_state_changes(
    monkeypatch, tamper, operation
):
    graph = PlanGraph(_steps())
    with monkeypatch.context() as m:
        _replace_policy(m, tamper)
        with pytest.raises(PlanConflictError, match="transition policy"):
            if operation == "construct":
                PlanGraph(_steps())
            elif operation == "ready":
                graph.ready_steps()
            elif operation == "statuses":
                graph.statuses()
            else:
                graph.transition("root", StepState.RUNNING, expected_revision=0)
    assert graph.statuses()["root"].state is StepState.PENDING
    assert graph.statuses()["root"].revision == 0


def test_modified_policy_cannot_skip_dependency_or_terminal_transition(monkeypatch):
    graph = PlanGraph(_steps())
    with monkeypatch.context() as m:
        _replace_policy(m, "direct_success")
        with pytest.raises(PlanConflictError, match="transition policy"):
            graph.transition("leaf", StepState.SUCCEEDED, expected_revision=0)
        with pytest.raises(PlanConflictError, match="transition policy"):
            graph.transition("root", StepState.SUCCEEDED, expected_revision=0)
    assert all(item.state is StepState.PENDING for item in graph.statuses().values())


def test_normal_planner_policy_keeps_terminal_propagation():
    graph = PlanGraph(_steps())
    root = graph.transition("root", StepState.RUNNING, expected_revision=0)
    graph.transition("root", StepState.FAILED, expected_revision=root.revision)
    assert graph.statuses()["root"].state is StepState.FAILED
    assert graph.statuses()["leaf"].state is StepState.BLOCKED
    assert graph.ready_steps() == ()
