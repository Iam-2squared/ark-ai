"""Run1099: direct PlanGraph state-machine and atomic-cascade regressions.

Only synthetic local plan state is used. No ToolBackend, permission grant,
dispatch, external effect, or automatic replay is involved.
"""

from __future__ import annotations

from types import MappingProxyType

import pytest

import ark.agency.planner as planner_module
from ark.agency import PlanConflictError, PlanGraph, PlanStep, StepState, ToolCall


def _steps() -> tuple[PlanStep, ...]:
    call = ToolCall("offline.read", "offline.read", "local-only", {"n": 1})
    return (
        PlanStep("root-a", call),
        PlanStep("root-b", call),
        PlanStep("join", call, ("root-a", "root-b")),
        PlanStep("leaf", call, ("join",)),
        PlanStep("isolated", call),
    )


def _status_rows(graph: PlanGraph) -> dict[str, tuple[StepState, int]]:
    return {
        name: (status.state, status.revision)
        for name, status in graph.statuses().items()
    }


def test_topology_identity_is_order_independent_but_keeps_edge_order() -> None:
    steps = _steps()
    original = PlanGraph(steps)
    reordered = PlanGraph(tuple(reversed(steps)))
    assert original.topology_digest() == reordered.topology_digest()

    edge_order_changed = tuple(
        PlanStep(step.step_id, step.call, tuple(reversed(step.depends_on)))
        if step.step_id == "join" else step
        for step in steps
    )
    assert PlanGraph(edge_order_changed).topology_digest() != original.topology_digest()


def test_ready_steps_and_terminal_failure_propagate_through_join_and_leaf() -> None:
    graph = PlanGraph(_steps())
    assert tuple(step.step_id for step in graph.ready_steps()) == (
        "isolated", "root-a", "root-b",
    )

    graph.transition("root-a", StepState.RUNNING, expected_revision=0)
    graph.transition("root-a", StepState.SUCCEEDED, expected_revision=1)
    graph.transition("root-b", StepState.RUNNING, expected_revision=0)
    graph.transition("root-b", StepState.FAILED, expected_revision=1)

    assert _status_rows(graph) == {
        "root-a": (StepState.SUCCEEDED, 2),
        "root-b": (StepState.FAILED, 2),
        "join": (StepState.BLOCKED, 1),
        "leaf": (StepState.BLOCKED, 1),
        "isolated": (StepState.PENDING, 0),
    }
    assert tuple(step.step_id for step in graph.ready_steps()) == ("isolated",)

    before = graph.status_digest()
    with pytest.raises(PlanConflictError, match="invalid transition"):
        graph.transition("root-a", StepState.RUNNING, expected_revision=2)
    with pytest.raises(PlanConflictError, match="invalid transition"):
        graph.transition("join", StepState.RUNNING, expected_revision=1)
    with pytest.raises(PlanConflictError, match="revision mismatch"):
        graph.transition("root-a", StepState.RUNNING, expected_revision=1)
    assert graph.status_digest() == before


def test_terminal_cascade_staging_failure_publishes_no_partial_status(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    graph = PlanGraph(_steps())
    graph.transition("root-a", StepState.RUNNING, expected_revision=0)
    before = _status_rows(graph)
    original_replace = planner_module.replace
    calls = 0

    def fail_while_staging_leaf(value: object, **changes: object) -> object:
        nonlocal calls
        calls += 1
        if calls == 3:
            raise RuntimeError("synthetic staged descendant failure")
        return original_replace(value, **changes)

    monkeypatch.setattr(planner_module, "replace", fail_while_staging_leaf)
    with pytest.raises(RuntimeError, match="staged descendant failure"):
        graph.transition("root-a", StepState.FAILED, expected_revision=1)
    assert calls == 3

    monkeypatch.setattr(planner_module, "replace", original_replace)
    assert _status_rows(graph) == before


def test_status_and_topology_views_are_detached_immutable_snapshots() -> None:
    graph = PlanGraph(_steps())
    snapshot = graph.statuses()
    assert type(snapshot) is MappingProxyType
    with pytest.raises(TypeError):
        snapshot["injected"] = snapshot["root-a"]  # type: ignore[index]
    with pytest.raises(TypeError):
        graph.steps["injected"] = graph.steps["root-a"]  # type: ignore[index]

    original_digest = graph.status_digest()
    object.__setattr__(snapshot["root-a"], "state", StepState.FAILED)
    assert graph.statuses()["root-a"].state is StepState.PENDING
    assert graph.status_digest() == original_digest


def test_exact_transition_ingress_rejects_subclasses_and_bool_revisions() -> None:
    graph = PlanGraph(_steps())
    invoked: list[str] = []

    class HostileStepId(str):
        def __hash__(self) -> int:
            invoked.append("hash")
            raise AssertionError("hostile step ID was hashed")

        def __eq__(self, other: object) -> bool:
            invoked.append("eq")
            raise AssertionError("hostile step ID was compared")

    with pytest.raises(TypeError, match="step_id"):
        graph.transition(HostileStepId("root-a"), StepState.RUNNING, expected_revision=0)
    with pytest.raises(TypeError, match="to_state"):
        graph.transition("root-a", "running", expected_revision=0)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="expected_revision"):
        graph.transition("root-a", StepState.RUNNING, expected_revision=True)
    assert invoked == []
    assert _status_rows(graph)["root-a"] == (StepState.PENDING, 0)
