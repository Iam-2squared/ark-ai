"""Deterministic offline DAG oracle for readiness propagation and blockers.

Probes are synthetic and do not attest to hardware, consent, or any executor.
"""

from __future__ import annotations

import random

import pytest

from ark.startup_readiness_review import (
    ReadinessState,
    StartupComponent,
    evaluate_startup_readiness,
)


@pytest.mark.parametrize("seed", (1, 2, 3, 4, 5, 6, 7, 8))
def test_readiness_dag_independent_oracle_and_order_invariance(seed: int) -> None:
    rng = random.Random(20261115 + seed)
    probes = []
    expected = {}
    parent_map = {}
    local_map = {}
    for index in range(14):
        name = f"local-{index:02d}"
        parents = tuple(
            f"local-{older:02d}"
            for older in range(index)
            if rng.randrange(5) == 0
        )
        local = rng.choice(
            (ReadinessState.READY, ReadinessState.DEGRADED, ReadinessState.BLOCKED)
        )
        parent_map[name] = parents
        local_map[name] = local
        if local is ReadinessState.BLOCKED:
            effective = ReadinessState.BLOCKED
        elif any(expected[parent] in (
            ReadinessState.BLOCKED, ReadinessState.DEPENDENCY_BLOCKED
        ) for parent in parents):
            effective = ReadinessState.DEPENDENCY_BLOCKED
        else:
            effective = local
        expected[name] = effective
        probes.append(StartupComponent(name, parents, local))

    ordered = evaluate_startup_readiness(probes)
    reversed_snapshot = evaluate_startup_readiness(reversed(probes))
    assert ordered.digest == reversed_snapshot.digest

    for name, effective in expected.items():
        assert ordered.state(name) is effective
        assert reversed_snapshot.state(name) is effective
        roots = set()
        frontier = [name]
        visited = set()
        while frontier:
            current = frontier.pop()
            if current in visited:
                continue
            visited.add(current)
            if local_map[current] is ReadinessState.BLOCKED:
                roots.add(current)
            else:
                frontier.extend(parent_map[current])
        assert ordered.root_blockers(name) == tuple(sorted(roots))


def test_degraded_dependency_does_not_implicitly_grant_or_block_child() -> None:
    snapshot = evaluate_startup_readiness((
        StartupComponent("local", local_state=ReadinessState.DEGRADED),
        StartupComponent("child", ("local",)),
    ))
    # A local DEGRADED state is diagnostic. Only BLOCKED propagates.
    assert snapshot.state("local") is ReadinessState.DEGRADED
    assert snapshot.state("child") is ReadinessState.READY
    assert snapshot.root_blockers("child") == ()


def test_readiness_cycle_cannot_be_reinterpreted_as_ready() -> None:
    with pytest.raises(ValueError, match="cycle"):
        evaluate_startup_readiness((
            StartupComponent("a", ("b",)),
            StartupComponent("b", ("a",)),
        ))
