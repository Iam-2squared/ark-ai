"""Terminal propagation is atomic when a descendant revision is exhausted."""

import pytest

from ark.agency import PlanConflictError, PlanGraph, PlanStep, StepState, ToolCall
from ark.agency.contracts import PlanStepStatus

MAX = (1 << 63) - 1


def plan_with_two_levels():
    return PlanGraph((
        PlanStep("root", ToolCall("fixture.read", "fixture.read", "local:scope")),
        PlanStep(
            "child",
            ToolCall("fixture.read", "fixture.read", "local:scope"),
            depends_on=("root",),
        ),
        PlanStep(
            "grandchild",
            ToolCall("fixture.read", "fixture.read", "local:scope"),
            depends_on=("child",),
        ),
        PlanStep("independent", ToolCall("fixture.read", "fixture.read", "local:scope")),
    ))


@pytest.mark.parametrize(
    "terminal",
    (StepState.FAILED, StepState.CANCELLED, StepState.BLOCKED),
)
@pytest.mark.parametrize("exhausted", ("child", "grandchild"))
def test_exhausted_descendant_leaves_entire_graph_unchanged(terminal, exhausted):
    graph = plan_with_two_levels()
    if terminal is not StepState.BLOCKED:
        graph.transition("root", StepState.RUNNING, expected_revision=0)
    graph._status[exhausted] = PlanStepStatus(exhausted, StepState.PENDING, MAX)
    before = dict(graph.statuses())

    revision = before["root"].revision
    with pytest.raises(PlanConflictError, match="dependent revision exhausted"):
        graph.transition("root", terminal, expected_revision=revision)
    assert dict(graph.statuses()) == before


def test_high_but_valid_descendant_revision_commits_whole_cascade():
    graph = plan_with_two_levels()
    graph._status["child"] = PlanStepStatus("child", StepState.PENDING, MAX - 1)
    result = graph.transition("root", StepState.BLOCKED, expected_revision=0)
    statuses = graph.statuses()
    assert result.state is StepState.BLOCKED
    assert statuses["root"].revision == 1
    assert statuses["child"].state is StepState.BLOCKED
    assert statuses["child"].revision == MAX
    assert statuses["grandchild"].state is StepState.BLOCKED
    assert statuses["grandchild"].revision == 1
    assert statuses["independent"].state is StepState.PENDING


def test_nonterminal_success_does_not_trigger_descendant_revision_preflight():
    graph = plan_with_two_levels()
    graph.transition("root", StepState.RUNNING, expected_revision=0)
    graph._status["child"] = PlanStepStatus("child", StepState.PENDING, MAX)
    result = graph.transition("root", StepState.SUCCEEDED, expected_revision=1)
    assert result.state is StepState.SUCCEEDED
    assert graph.statuses()["child"].revision == MAX
