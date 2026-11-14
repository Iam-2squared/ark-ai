"""Deep synthetic plan graph validation, no ToolBackend execution."""

import pytest

from ark.agency.contracts import PlanStep, StepState, ToolCall
from ark.agency.planner import PlanGraph


def _fixture_steps(count, *, cycle=False):
    call = ToolCall(
        "fixture.read", "fixture.read", "synthetic:owner", {"fixture": True}
    )
    return tuple(
        PlanStep(
            f"step-{index:04d}",
            call,
            (
                (f"step-{count - 1:04d}",)
                if cycle and index == 0
                else (f"step-{index - 1:04d}",) if index else ()
            ),
        )
        for index in range(count)
    )


def test_deep_chain_passes_without_python_recursion_limit():
    graph = PlanGraph(_fixture_steps(1500))
    assert tuple(step.step_id for step in graph.ready_steps()) == ("step-0000",)
    started = graph.transition("step-0000", StepState.RUNNING, expected_revision=0)
    assert started.revision == 1
    graph.transition("step-0000", StepState.SUCCEEDED, expected_revision=1)
    assert tuple(step.step_id for step in graph.ready_steps()) == ("step-0001",)


def test_deep_cycle_rejected_as_plan_error_not_recursion_error():
    with pytest.raises(ValueError, match="cycle"):
        PlanGraph(_fixture_steps(1500, cycle=True))


def test_shared_transitive_dependencies_are_not_falsely_flagged():
    call = ToolCall("fixture.read", "fixture.read", "synthetic:owner", {})
    graph = PlanGraph(
        (
            PlanStep("root", call),
            PlanStep("left", call, ("root",)),
            PlanStep("right", call, ("root",)),
            PlanStep("join", call, ("left", "right")),
        )
    )
    assert len(graph.statuses()) == 4
    assert tuple(step.step_id for step in graph.ready_steps()) == ("root",)
