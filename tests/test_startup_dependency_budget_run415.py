"""Bounded disconnected startup graphs cannot consume unbounded fan-in.

A READY probe is synthetic diagnostic input, never permission to start tools,
external services, hardware, notifications or model inference.
"""

import pytest

from ark.startup_readiness_review import (
    ComponentResult,
    ReadinessState,
    StartupComponent,
    StartupSnapshot,
    evaluate_startup_readiness,
)


def _wide_graph(child_count: int):
    roots = tuple(StartupComponent(f"root-{i}") for i in range(1024))
    dependencies = tuple(root.component_id for root in roots)
    children = tuple(
        StartupComponent(f"child-{i}", dependencies)
        for i in range(child_count)
    )
    return roots + children


def test_single_component_fan_in_budget_refuses_oversize_tuple():
    dependencies = tuple(f"root-{i}" for i in range(4097))
    with pytest.raises(ValueError, match="per-component dependency budget"):
        StartupComponent("consumer", dependencies)


def test_generator_stops_at_first_edge_budget_violation():
    produced = 0

    def probes():
        nonlocal produced
        for component in _wide_graph(65):
            produced += 1
            yield component

    with pytest.raises(ValueError, match="dependency budget"):
        evaluate_startup_readiness(probes())
    assert produced == 1024 + 65


def test_exact_aggregate_edge_budget_is_accepted_but_inert():
    snapshot = evaluate_startup_readiness(_wide_graph(64))
    assert snapshot.state("child-63") is ReadinessState.READY
    assert snapshot.root_blockers("child-63") == ()


def test_forged_cached_snapshot_cannot_exceed_edge_budget():
    roots = tuple(
        ComponentResult(f"root-{i}", (), ReadinessState.READY,
                        ReadinessState.READY, None, None)
        for i in range(1024)
    )
    names = tuple(sorted(item.component_id for item in roots))
    children = tuple(
        ComponentResult(f"child-{i}", names, ReadinessState.READY,
                        ReadinessState.READY, None, None)
        for i in range(65)
    )
    snapshot = StartupSnapshot(
        tuple(sorted(roots + children, key=lambda item: item.component_id)),
        "startup_" + "0" * 64,
    )
    with pytest.raises(ValueError, match="snapshot dependency budget"):
        snapshot.state("child-0")


def test_reflectively_oversized_component_cannot_enter_readiness():
    root = StartupComponent("root")
    consumer = StartupComponent("consumer", ("root",))
    object.__setattr__(
        consumer, "dependencies", tuple(f"edge-{i}" for i in range(4097)),
    )
    with pytest.raises(ValueError, match="per-component dependency budget"):
        evaluate_startup_readiness((root, consumer))
