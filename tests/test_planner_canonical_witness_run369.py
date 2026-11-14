"""Disconnected canonical plan input/state digests for future recovery."""

import re

import pytest

from ark.agency.contracts import PlanConflictError, PlanStep, StepState, ToolCall
from ark.agency.planner import PlanGraph


def _step(name: str, value: int, dependencies=()):
    return PlanStep(
        name,
        ToolCall("offline", "fixture", "test", {"content": value}),
        dependencies,
    )


def _graph(order=("root", "left", "right", "join"), join_deps=("left", "right")):
    entries = {
        "root": _step("root", 1),
        "left": _step("left", 2, ("root",)),
        "right": _step("right", 3, ("root",)),
        "join": _step("join", 4, join_deps),
    }
    return PlanGraph(tuple(entries[name] for name in order))


def test_plan_witnesses_stable_across_step_registration_order():
    first = _graph()
    second = _graph(("join", "right", "root", "left"))
    assert first.topology_digest() == second.topology_digest()
    assert first.status_digest() == second.status_digest()
    assert re.fullmatch(r"plan_[0-9a-f]{64}", first.topology_digest())
    assert re.fullmatch(r"pstate_[0-9a-f]{64}", first.status_digest())


def test_topology_digest_binds_explicit_dependency_tuple_order():
    assert _graph().topology_digest() != _graph(
        join_deps=("right", "left")
    ).topology_digest()


def test_modified_canonical_toolcall_changes_topology_and_status_witness():
    first = PlanGraph((_step("step", 1),))
    changed = PlanGraph((_step("step", 2),))
    assert first.topology_digest() != changed.topology_digest()
    assert first.status_digest() != changed.status_digest()


def test_status_digest_changes_on_transitions_but_topology_is_stable():
    graph = _graph()
    identity = graph.topology_digest()
    witnesses = {graph.status_digest()}
    graph.transition("root", StepState.RUNNING, expected_revision=0)
    witnesses.add(graph.status_digest())
    graph.transition("root", StepState.SUCCEEDED, expected_revision=1)
    witnesses.add(graph.status_digest())
    graph.transition("left", StepState.RUNNING, expected_revision=0)
    witnesses.add(graph.status_digest())
    graph.transition("left", StepState.FAILED, expected_revision=1)
    witnesses.add(graph.status_digest())
    assert len(witnesses) == 5
    assert graph.topology_digest() == identity
    assert graph.statuses()["join"].state is StepState.BLOCKED
    assert graph.statuses()["join"].revision == 1
    assert graph.statuses()["right"].state is StepState.PENDING


def test_reflected_toolcall_change_rejected_before_canonical_digest():
    step = _step("root", 1)
    graph = PlanGraph((step,))
    object.__setattr__(step.call, "scope", "retargeted")
    with pytest.raises(PlanConflictError):
        graph.topology_digest()
    with pytest.raises(PlanConflictError):
        graph.status_digest()


def test_status_snapshot_identity_corruption_cannot_be_hashed_as_valid():
    graph = PlanGraph((_step("root", 1),))
    object.__setattr__(graph._status["root"], "step_id", "different")
    with pytest.raises(PlanConflictError, match="status identity"):
        graph.status_digest()


def test_deep_topology_witness_does_not_recurse():
    steps = [_step("node-0", 0)]
    for index in range(1, 1501):
        steps.append(_step(f"node-{index}", index, (f"node-{index - 1}",)))
    graph = PlanGraph(tuple(steps))
    assert graph.topology_digest().startswith("plan_")
    assert graph.status_digest().startswith("pstate_")
