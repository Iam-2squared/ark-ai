"""PlanGraph witness construction must not return a stale plan/status epoch.

All mutations below are synthetic in-process fault hooks; these checks do not
provide authorization, external backend replay permission, or clock attestation.
"""

from dataclasses import replace as dataclass_replace

import pytest

import ark.agency.planner as planner_module
from ark.agency.contracts import PlanConflictError, PlanStep, StepState, ToolCall
from ark.agency.planner import PlanGraph


def _graph() -> tuple[PlanGraph, PlanStep, PlanStep]:
    root = PlanStep("root", ToolCall("offline.read", "read", "local"))
    child = PlanStep(
        "child", ToolCall("offline.write", "write", "local"), ("root",)
    )
    return PlanGraph((root, child)), root, child


@pytest.mark.parametrize("mutate", ["call_carrier", "dependencies_carrier"])
def test_topology_hash_rejects_late_original_input_replacement(
    monkeypatch: pytest.MonkeyPatch, mutate: str,
) -> None:
    graph, root, child = _graph()
    prior_hash = planner_module._plan_digest

    def hashing(label: str, payload: object) -> str:
        witness = prior_hash(label, payload)
        if label == "plan_":
            if mutate == "call_carrier":
                object.__setattr__(
                    root, "call", ToolCall("offline.read", "read", "local")
                )
            else:
                object.__setattr__(child, "depends_on", tuple(["root"]))
        return witness

    monkeypatch.setattr(planner_module, "_plan_digest", hashing)
    with pytest.raises(PlanConflictError, match="changed"):
        graph.topology_digest()


@pytest.mark.parametrize("mutate", ["status_field", "status_mapping", "call_scope"])
def test_status_hash_rejects_late_state_or_plan_retargeting(
    monkeypatch: pytest.MonkeyPatch, mutate: str,
) -> None:
    graph, root, _child = _graph()
    prior_hash = planner_module._plan_digest

    def hashing(label: str, payload: object) -> str:
        witness = prior_hash(label, payload)
        if label == "pstate_":
            if mutate == "status_field":
                object.__setattr__(
                    graph._status["root"], "state", StepState.SUCCEEDED
                )
            elif mutate == "status_mapping":
                graph._status = dict(graph._status)
            else:
                object.__setattr__(root.call, "scope", "retargeted")
        return witness

    monkeypatch.setattr(planner_module, "_plan_digest", hashing)
    with pytest.raises(PlanConflictError):
        graph.status_digest()


@pytest.mark.parametrize("mutate", ["status_field", "status_mapping"])
def test_detached_snapshot_rejects_late_authoritative_state_replacement(
    monkeypatch: pytest.MonkeyPatch, mutate: str,
) -> None:
    graph, _root, _child = _graph()
    original_replace = dataclass_replace

    def replacing(value, **kwargs):
        copied = original_replace(value, **kwargs)
        if value.step_id == "root":
            if mutate == "status_field":
                object.__setattr__(
                    graph._status["child"], "revision", 99
                )
            else:
                graph._status = dict(graph._status)
        return copied

    monkeypatch.setattr(planner_module, "replace", replacing)
    with pytest.raises(PlanConflictError, match="status"):
        graph.statuses()


def test_witnesses_and_detached_statuses_remain_stable_without_faults() -> None:
    graph, _root, _child = _graph()
    topology = graph.topology_digest()
    initial = graph.status_digest()
    assert topology.startswith("plan_")
    assert initial.startswith("pstate_")
    assert graph.topology_digest() == topology
    assert graph.status_digest() == initial
    assert graph.statuses()["root"].state is StepState.PENDING

    graph.transition("root", StepState.RUNNING, expected_revision=0)
    graph.transition("root", StepState.SUCCEEDED, expected_revision=1)
    assert graph.topology_digest() == topology
    assert graph.status_digest() != initial
    assert tuple(step.step_id for step in graph.ready_steps()) == ("child",)
