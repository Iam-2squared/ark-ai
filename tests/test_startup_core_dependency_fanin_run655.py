"""Non-UI startup dependency gates remain diagnostic, never authority.

The graph uses synthetic component assertions; no real probe, account,
tool, notification, device, or background scheduler is started.
"""

from __future__ import annotations

import pytest

from ark.startup_readiness_review import (
    ReadinessState,
    StartupComponent,
    evaluate_startup_readiness,
)


def _graph(*, memory: ReadinessState, audit: ReadinessState):
    return (
        StartupComponent("memory", local_state=memory, schema_revision="v1"),
        StartupComponent("planner", ("memory",), schema_revision="v1"),
        StartupComponent("registry", schema_revision="v1"),
        StartupComponent("permissions", ("registry",), schema_revision="v1"),
        StartupComponent("audit", local_state=audit, schema_revision="v1"),
        StartupComponent(
            "write_executor", ("planner", "permissions", "audit"),
            schema_revision="mock-only",
        ),
        StartupComponent("private_context", ("memory",)),
        StartupComponent(
            "observation", local_state=ReadinessState.DEGRADED,
            failure_code="fixture_only",
        ),
        StartupComponent("proactive_preview", ("private_context", "observation")),
        StartupComponent("recovery", ("planner", "audit")),
    )


@pytest.mark.parametrize("blocked", ("memory", "audit"))
def test_blocked_core_cannot_present_write_or_recovery_as_ready(blocked):
    probes = _graph(
        memory=ReadinessState.BLOCKED if blocked == "memory" else ReadinessState.READY,
        audit=ReadinessState.BLOCKED if blocked == "audit" else ReadinessState.READY,
    )
    snapshot = evaluate_startup_readiness(probes)
    assert snapshot.state("write_executor") is ReadinessState.DEPENDENCY_BLOCKED
    assert snapshot.state("recovery") is ReadinessState.DEPENDENCY_BLOCKED
    assert snapshot.root_blockers("write_executor") == (blocked,)
    assert snapshot.root_blockers("recovery") == (blocked,)
    assert snapshot.state("permissions") is ReadinessState.READY
    assert snapshot.state("observation") is ReadinessState.DEGRADED
    expected_context = (
        ReadinessState.DEPENDENCY_BLOCKED
        if blocked == "memory" else ReadinessState.READY
    )
    assert snapshot.state("private_context") is expected_context
    assert snapshot.state("proactive_preview") is expected_context
    assert snapshot.root_blockers("proactive_preview") == (
        ("memory",) if blocked == "memory" else ()
    )
    # These statuses only restate synthetic probes, not activation authority.


def test_synthetic_readiness_identity_is_independent_of_probe_iteration_order():
    probes = _graph(memory=ReadinessState.BLOCKED, audit=ReadinessState.READY)
    forward = evaluate_startup_readiness(probes)
    reverse = evaluate_startup_readiness(reversed(probes))
    assert forward.digest == reverse.digest
    assert forward.components == reverse.components
    assert forward.state("write_executor") is ReadinessState.DEPENDENCY_BLOCKED
    assert reverse.root_blockers("write_executor") == ("memory",)


def test_reflected_cached_ready_forgery_cannot_hide_blocked_dependency():
    snapshot = evaluate_startup_readiness(
        _graph(memory=ReadinessState.BLOCKED, audit=ReadinessState.READY)
    )
    forged = next(
        item for item in snapshot.components if item.component_id == "write_executor"
    )
    object.__setattr__(forged, "effective_state", ReadinessState.READY)
    with pytest.raises(ValueError, match="effective state changed"):
        snapshot.state("write_executor")
    with pytest.raises(ValueError, match="effective state changed"):
        snapshot.root_blockers("write_executor")
