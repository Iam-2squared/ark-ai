"""Independent cancellation oracle for reversible in-memory Planner DAGs.

No tool dispatch, persistent journal mutation or external side effects.
"""

import pytest

from ark.agency.contracts import PlanConflictError, PlanStep, StepState, ToolCall
from ark.agency.planner import PlanGraph


def steps(seed, count):
    return tuple(
        PlanStep(
            f"p{i:02d}",
            ToolCall("mock.read", "fixture", "local", {"i": i}),
            tuple(
                f"p{j:02d}" for j in range(i)
                if (j * 7 + i * 11 + seed) % 6 == 0
                or (j == 0 and i % 3 == 0)
            ),
        )
        for i in range(count)
    )


@pytest.mark.parametrize("seed", range(8))
def test_cancellation_matches_transitive_pending_descendant_oracle(seed):
    source = steps(seed, 31)
    dependencies = {step.step_id: step.depends_on for step in source}
    graph = PlanGraph(source)
    reversed_graph = PlanGraph(tuple(reversed(source)))
    topology = graph.topology_digest()
    assert reversed_graph.topology_digest() == topology
    for candidate in (graph, reversed_graph):
        started = candidate.transition("p00", StepState.RUNNING, expected_revision=0)
        assert (started.state, started.revision) == (StepState.RUNNING, 1)
        cancelled = candidate.transition(
            "p00", StepState.CANCELLED, expected_revision=1,
        )
        assert (cancelled.state, cancelled.revision) == (StepState.CANCELLED, 2)

    descendants = {"p00"}
    while True:
        expanded = descendants | {
            step for step, deps in dependencies.items()
            if set(deps) & descendants
        }
        if expanded == descendants:
            break
        descendants = expanded

    for candidate in (graph, reversed_graph):
        statuses = candidate.statuses()
        for name in dependencies:
            expected = (
                StepState.CANCELLED if name == "p00"
                else StepState.BLOCKED if name in descendants
                else StepState.PENDING
            )
            assert statuses[name].state is expected
            assert statuses[name].revision == (
                2 if name == "p00" else 1 if name in descendants else 0
            )
        assert {step.step_id for step in candidate.ready_steps()} == {
            name for name, deps in dependencies.items()
            if name not in descendants and not deps
        }
    assert graph.status_digest() == reversed_graph.status_digest()
    assert graph.topology_digest() == topology


def test_stale_revision_cannot_reanimate_cancelled_descendants():
    root = PlanStep("root", ToolCall("mock.read", "fixture", "local"))
    child = PlanStep(
        "child", ToolCall("mock.read", "fixture", "local"), ("root",),
    )
    grandchild = PlanStep(
        "grandchild", ToolCall("mock.read", "fixture", "local"), ("child",),
    )
    independent = PlanStep("independent", ToolCall("mock.read", "fixture", "local"))
    graph = PlanGraph((root, child, grandchild, independent))
    graph.transition("root", StepState.CANCELLED, expected_revision=0)
    digest = graph.status_digest()
    assert {step.step_id for step in graph.ready_steps()} == {"independent"}
    for name in ("child", "grandchild"):
        with pytest.raises(PlanConflictError, match="revision mismatch"):
            graph.transition(name, StepState.RUNNING, expected_revision=0)
        assert graph.statuses()[name].state is StepState.BLOCKED
    assert graph.status_digest() == digest


def test_detached_status_mutation_does_not_corrupt_cancellation_journal():
    source = steps(3, 12)
    graph = PlanGraph(source)
    graph.transition("p00", StepState.CANCELLED, expected_revision=0)
    expected = graph.status_digest()
    detached = graph.statuses()
    object.__setattr__(detached["p00"], "revision", 99)
    assert graph.statuses()["p00"].revision == 1
    assert graph.status_digest() == expected
