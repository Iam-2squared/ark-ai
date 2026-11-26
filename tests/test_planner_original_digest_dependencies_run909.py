"""Disconnected Planner digests must reject substituted codec dependencies.

These are only local integrity witnesses. Rejecting a poisoned hash neither
grants execution authority nor rolls back an existing durable side effect.
"""

import pytest

import ark.agency.planner as planner
from ark.agency import PlanConflictError, PlanGraph, PlanStep, StepState, ToolCall


def _steps():
    call = ToolCall("fixture.read", "fixture.read", "offline")
    return (
        PlanStep("root", call),
        PlanStep("dependent", call, ("root",)),
    )


@pytest.mark.parametrize("dependency", ["sha256", "dumps"])
@pytest.mark.parametrize("operation", ["topology_digest", "status_digest", "transition"])
def test_poisoned_digest_function_denies_before_read_or_status_mutation(
    monkeypatch, dependency, operation,
):
    graph = PlanGraph(_steps())
    earlier = graph.status_digest()
    invoked = []

    def forbidden(*args, **kwargs):
        invoked.append((args, kwargs))
        raise AssertionError("substituted Planner digest executed")

    module = planner.hashlib if dependency == "sha256" else planner.json
    with monkeypatch.context() as patch:
        patch.setattr(module, dependency, forbidden)
        with pytest.raises(PlanConflictError, match="digest dependencies"):
            if operation == "transition":
                graph.transition("root", StepState.RUNNING, expected_revision=0)
            else:
                getattr(graph, operation)()
    assert invoked == []
    assert graph.status_digest() == earlier
    assert graph.statuses()["root"].state is StepState.PENDING


@pytest.mark.parametrize("dependency", ["hashlib", "json"])
def test_poisoned_module_refused_during_graph_construction(monkeypatch, dependency):
    steps = _steps()
    with monkeypatch.context() as patch:
        patch.setattr(planner, dependency, object())
        with pytest.raises(PlanConflictError, match="digest dependencies"):
            PlanGraph(steps)


@pytest.mark.parametrize("dependency", ["sha256", "dumps"])
def test_direct_digest_refuses_substituted_serializer(monkeypatch, dependency):
    invoked = []

    def forbidden(*args, **kwargs):
        invoked.append((args, kwargs))
        raise AssertionError("substituted digest ran")

    module = planner.hashlib if dependency == "sha256" else planner.json
    with monkeypatch.context() as patch:
        patch.setattr(module, dependency, forbidden)
        with pytest.raises(PlanConflictError, match="digest dependencies"):
            planner._plan_digest("plan_", {"schema_version": 1})
    assert invoked == []


def test_late_helper_change_refuses_stale_topology_receipt(monkeypatch):
    graph = PlanGraph(_steps())
    original = planner._plan_digest
    called = []

    with monkeypatch.context() as patch:
        def late_change(prefix, payload):
            receipt = original(prefix, payload)
            if prefix == "plan_":
                called.append("plan")
                patch.setattr(planner, "json", object())
            return receipt

        patch.setattr(planner, "_plan_digest", late_change)
        with pytest.raises(PlanConflictError, match="digest dependencies"):
            graph.topology_digest()
    assert called == ["plan"]
    assert graph.statuses()["root"].state is StepState.PENDING


def test_unmodified_planner_digest_remains_deterministic_and_denial_only():
    graph = PlanGraph(_steps())
    topo = graph.topology_digest()
    status = graph.status_digest()
    assert topo == graph.topology_digest()
    assert status == graph.status_digest()
    graph.transition("root", StepState.RUNNING, expected_revision=0)
    assert graph.status_digest() != status
    assert graph.topology_digest() == topo
