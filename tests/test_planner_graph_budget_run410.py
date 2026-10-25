"""Standalone Planner DAG ingress budgets, disconnected/no executor."""

import pytest

from ark.agency.contracts import PlanConflictError, PlanStep, ToolCall
from ark.agency.planner import PlanGraph

CALL = ToolCall("offline.read", "offline.read", "local")


def _steps(n):
    return tuple(PlanStep(f"step-{index}", CALL) for index in range(n))


def _dense(leaves):
    roots = tuple(PlanStep(f"root-{index}", CALL) for index in range(256))
    edges = tuple(f"root-{index}" for index in range(256))
    children = tuple(
        PlanStep(f"child-{index}", CALL, edges) for index in range(leaves)
    )
    return roots + children


def test_overlarge_step_graph_fails_before_construction():
    with pytest.raises(ValueError, match="step budget"):
        PlanGraph(_steps(4097))


def test_step_limit_accepts_valid_deep_free_graph():
    graph = PlanGraph(_steps(4096))
    assert len(graph.ready_steps()) == 4096


def test_exact_edge_limit_is_accepted():
    graph = PlanGraph(_dense(256))
    assert len(graph.ready_steps()) == 256


def test_excessive_total_dependency_edges_are_rejected():
    with pytest.raises(ValueError, match="dependency budget"):
        PlanGraph(_dense(257))


def test_reflected_unbounded_dependency_carrier_rejected_without_iteration():
    class NeverIterate:
        def __iter__(self):
            raise AssertionError("unbounded dependency source was consumed")

    step = PlanStep("safe", CALL)
    object.__setattr__(step, "depends_on", NeverIterate())
    with pytest.raises(PlanConflictError, match="dependency carrier"):
        PlanGraph((step,))
