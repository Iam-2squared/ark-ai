"""Synthetic lane-scoped readiness cannot implicitly enable live execution."""

import random

import pytest

from ark.startup_readiness_review import (
    ReadinessState,
    StartupComponent,
    evaluate_startup_readiness,
)

READY = ReadinessState.READY
BLOCKED = ReadinessState.BLOCKED
DEPENDENCY_BLOCKED = ReadinessState.DEPENDENCY_BLOCKED


def _components():
    return (
        StartupComponent("memory", local_state=BLOCKED, failure_code="schema_mismatch"),
        StartupComponent("personal_context", ("memory",)),
        StartupComponent("conversation"),
        StartupComponent("audit", local_state=BLOCKED, failure_code="journal_corrupt"),
        StartupComponent("durable_auth", local_state=READY),
        StartupComponent("write_executor", ("audit", "durable_auth")),
        StartupComponent("read_executor"),
        StartupComponent("planner_recovery", local_state=BLOCKED),
        StartupComponent("task_resume", ("planner_recovery",)),
        StartupComponent("vision", local_state=BLOCKED),
        StartupComponent("text_lane"),
    )


def test_lane_scoped_blocks_preserve_unrelated_capabilities():
    snapshot = evaluate_startup_readiness(_components())
    assert snapshot.state("personal_context") is DEPENDENCY_BLOCKED
    assert snapshot.state("write_executor") is DEPENDENCY_BLOCKED
    assert snapshot.state("task_resume") is DEPENDENCY_BLOCKED
    assert snapshot.state("memory") is BLOCKED
    assert snapshot.state("conversation") is READY
    assert snapshot.state("read_executor") is READY
    assert snapshot.state("text_lane") is READY
    assert snapshot.root_blockers("write_executor") == ("audit",)
    assert snapshot.root_blockers("personal_context") == ("memory",)
    assert snapshot.root_blockers("task_resume") == ("planner_recovery",)


def test_randomized_order_and_dependency_order_preserve_digest():
    canonical = evaluate_startup_readiness(_components()).digest
    rng = random.Random(367)
    for _ in range(250):
        permuted = list(_components())
        rng.shuffle(permuted)
        reversed_edges = [
            StartupComponent(
                item.component_id,
                tuple(reversed(item.dependencies)),
                item.local_state,
                item.failure_code,
                item.schema_revision,
            )
            for item in permuted
        ]
        assert evaluate_startup_readiness(reversed_edges).digest == canonical


@pytest.mark.parametrize(
    ("specs", "message"),
    [
        ((StartupComponent("a"), StartupComponent("a")), "duplicate"),
        ((StartupComponent("a", ("missing",)),), "unknown"),
        (
            (StartupComponent("a", ("b",)), StartupComponent("b", ("a",))),
            "cycle",
        ),
    ],
)
def test_invalid_graph_rejected(specs, message):
    with pytest.raises(ValueError, match=message):
        evaluate_startup_readiness(specs)


def test_empty_graph_and_self_dependency_rejected():
    with pytest.raises(ValueError, match="at least one"):
        evaluate_startup_readiness([])
    with pytest.raises(ValueError, match="itself"):
        StartupComponent("a", ("a",))


def test_duplicate_edges_and_derived_state_as_local_are_invalid():
    with pytest.raises(ValueError, match="duplicate"):
        StartupComponent("a", ("b", "b"))
    with pytest.raises(ValueError, match="cannot be supplied"):
        StartupComponent("a", local_state=DEPENDENCY_BLOCKED)


def test_degraded_does_not_get_upgraded_to_ready():
    snapshot = evaluate_startup_readiness((
        StartupComponent("local", local_state=ReadinessState.DEGRADED),
        StartupComponent("consumer", ("local",)),
    ))
    assert snapshot.state("local") is ReadinessState.DEGRADED
    assert snapshot.state("consumer") is READY


def test_revalidation_changes_digest_and_keeps_old_snapshot_stable():
    before = evaluate_startup_readiness(_components())
    replaced = tuple(
        StartupComponent(
            item.component_id, item.dependencies,
            READY if item.component_id == "memory" else item.local_state,
            item.failure_code, item.schema_revision,
        )
        for item in _components()
    )
    after = evaluate_startup_readiness(replaced)
    assert before.digest != after.digest
    assert before.state("personal_context") is DEPENDENCY_BLOCKED
    assert after.state("personal_context") is READY
    with pytest.raises(KeyError, match="unknown"):
        after.state("absent")


def test_deep_dependency_chain_is_iterative():
    specs = [StartupComponent("node-0", local_state=BLOCKED)]
    specs.extend(
        StartupComponent(f"node-{i}", (f"node-{i - 1}",))
        for i in range(1, 1501)
    )
    snapshot = evaluate_startup_readiness(specs)
    assert snapshot.state("node-1500") is DEPENDENCY_BLOCKED
    assert snapshot.root_blockers("node-1500") == ("node-0",)
