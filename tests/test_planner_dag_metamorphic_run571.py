"""Deterministic DAG-oracle regression tests for local-only Planner state."""

import pytest

from ark.agency.contracts import PlanStep, StepState, ToolCall
from ark.agency.planner import PlanGraph


def _steps(seed, size):
    result = []
    for index in range(size):
        deps = tuple(
            f"s{other:02d}" for other in range(index)
            if (index * 17 + other * 11 + seed) % 5 == 0
            or (index % 4 == 0 and other == 0)
        )
        result.append(PlanStep(
            f"s{index:02d}",
            ToolCall("mock.read", "fixture", "local", {"index": index}),
            deps,
        ))
    return tuple(result)


@pytest.mark.parametrize("seed", range(8))
@pytest.mark.parametrize("size", (1, 7, 23))
def test_ready_frontier_matches_independent_dag_oracle(seed, size):
    steps = _steps(seed, size)
    graph = PlanGraph(steps)
    reversed_graph = PlanGraph(tuple(reversed(steps)))
    assert graph.topology_digest() == reversed_graph.topology_digest()
    assert graph.status_digest() == reversed_graph.status_digest()
    dag = {step.step_id: step.depends_on for step in steps}
    succeeded = set()
    while len(succeeded) < len(steps):
        pending = set(dag) - succeeded
        expected = sorted(
            step for step in pending
            if all(dep in succeeded for dep in dag[step])
        )
        actual = sorted(step.step_id for step in graph.ready_steps())
        assert actual == expected
        assert expected  # every nonempty DAG must expose a ready frontier
        for step in reversed(expected):
            running = graph.transition(
                step, StepState.RUNNING, expected_revision=0,
            )
            assert running.state is StepState.RUNNING
            assert running.revision == 1
            success = graph.transition(
                step, StepState.SUCCEEDED, expected_revision=1,
            )
            assert success.state is StepState.SUCCEEDED
            assert success.revision == 2
            succeeded.add(step)
    assert graph.ready_steps() == ()
    assert all(row.state is StepState.SUCCEEDED
               for row in graph.statuses().values())


@pytest.mark.parametrize("seed", range(8))
@pytest.mark.parametrize("terminal", ("blocked", "failed"))
def test_terminal_cascade_matches_transitive_dependency_oracle(seed, terminal):
    steps = _steps(seed, 23)
    dag = {step.step_id: step.depends_on for step in steps}
    graph = PlanGraph(steps)
    if terminal == "failed":
        graph.transition("s00", StepState.RUNNING, expected_revision=0)
        graph.transition("s00", StepState.FAILED, expected_revision=1)
        root_state, root_revision = StepState.FAILED, 2
    else:
        graph.transition("s00", StepState.BLOCKED, expected_revision=0)
        root_state, root_revision = StepState.BLOCKED, 1
    descendants = {"s00"}
    while True:
        expanded = descendants | {
            step for step, dependencies in dag.items()
            if set(dependencies) & descendants
        }
        if expanded == descendants:
            break
        descendants = expanded
    states = graph.statuses()
    assert states["s00"].state is root_state
    assert states["s00"].revision == root_revision
    for step in dag:
        if step == "s00":
            continue
        expected_state = (
            StepState.BLOCKED if step in descendants else StepState.PENDING
        )
        assert states[step].state is expected_state
        assert states[step].revision == (1 if step in descendants else 0)
    assert set(item.step_id for item in graph.ready_steps()) == {
        step for step in dag if step not in descendants and not dag[step]
    }


def test_cycle_rejected_without_recursive_stack():
    a = PlanStep("a", ToolCall("fake.read", "fixture", "local"), ("b",))
    b = PlanStep("b", ToolCall("fake.read", "fixture", "local"), ("a",))
    with pytest.raises(ValueError, match="cycle"):
        PlanGraph((a, b))
