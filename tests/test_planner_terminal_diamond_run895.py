"""Disconnected Planner diamond: terminal propagation, exact revisions and fan-in.

Only synthetic READ steps; no registry dispatch, approval, model, or side effect.
"""
import pytest

from ark.agency.contracts import PlanConflictError, PlanStep, StepState, ToolCall
from ark.agency.planner import PlanGraph


def _diamond() -> PlanGraph:
    dependencies = (
        ("root", ()),
        ("left", ("root",)),
        ("right", ("root",)),
        ("join", ("left", "right")),
        ("unrelated", ()),
    )
    return PlanGraph(tuple(
        PlanStep(
            name,
            ToolCall("fixture.inspect", "fixture.read", "synthetic", {"name": name}),
            depends_on=needs,
        )
        for name, needs in dependencies
    ))


def _ready(graph: PlanGraph) -> set[str]:
    return {step.step_id for step in graph.ready_steps()}


@pytest.mark.parametrize("terminal", (StepState.FAILED, StepState.CANCELLED))
def test_terminal_root_blocks_shared_descendant_once_and_preserves_unrelated(terminal):
    graph = _diamond()
    before_topology = graph.topology_digest()
    assert _ready(graph) == {"root", "unrelated"}
    graph.transition("root", StepState.RUNNING, expected_revision=0)
    graph.transition("root", terminal, expected_revision=1)

    statuses = graph.statuses()
    assert statuses["root"].state is terminal
    assert statuses["root"].revision == 2
    assert {statuses[name].state for name in ("left", "right", "join")} == {
        StepState.BLOCKED
    }
    assert {statuses[name].revision for name in ("left", "right", "join")} == {1}
    assert statuses["unrelated"].state is StepState.PENDING
    assert statuses["unrelated"].revision == 0
    assert _ready(graph) == {"unrelated"}
    assert graph.topology_digest() == before_topology
    with pytest.raises(PlanConflictError):
        graph.transition("join", StepState.RUNNING, expected_revision=1)
    with pytest.raises(PlanConflictError):
        graph.transition("root", StepState.RUNNING, expected_revision=2)
    assert graph.statuses() == statuses


def test_diamond_join_waits_for_both_successes_and_remains_single_runnable_step():
    graph = _diamond()
    graph.transition("root", StepState.RUNNING, expected_revision=0)
    graph.transition("root", StepState.SUCCEEDED, expected_revision=1)
    assert _ready(graph) == {"left", "right", "unrelated"}
    graph.transition("left", StepState.RUNNING, expected_revision=0)
    graph.transition("left", StepState.SUCCEEDED, expected_revision=1)
    assert "join" not in _ready(graph)
    graph.transition("right", StepState.RUNNING, expected_revision=0)
    graph.transition("right", StepState.SUCCEEDED, expected_revision=1)
    assert _ready(graph) == {"join", "unrelated"}
    graph.transition("join", StepState.RUNNING, expected_revision=0)
    graph.transition("join", StepState.SUCCEEDED, expected_revision=1)
    assert graph.statuses()["join"].revision == 2
    assert _ready(graph) == {"unrelated"}


def test_failed_dependency_cascade_does_not_advance_unrelated_status_epoch():
    graph = _diamond()
    original_digest = graph.status_digest()
    original_unrelated = graph.statuses()["unrelated"]
    graph.transition("root", StepState.RUNNING, expected_revision=0)
    graph.transition("root", StepState.FAILED, expected_revision=1)
    assert graph.status_digest() != original_digest
    assert graph.statuses()["unrelated"] == original_unrelated
    # An unrelated safe READ preview can still advance its independent state.
    graph.transition("unrelated", StepState.RUNNING, expected_revision=0)
    assert _ready(graph) == set()
    assert graph.statuses()["join"].revision == 1
