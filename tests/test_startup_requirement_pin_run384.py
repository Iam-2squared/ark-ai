"""Startup readiness must check pinned requirements despite reentrant changes."""

import pytest

from ark.startup_readiness_lease_review import (
    SyntheticReadinessRequirement,
    SyntheticStartupLeaseRejected,
    review_synthetic_startup_lease,
)
from ark.startup_readiness_review import (
    ReadinessState,
    StartupComponent,
    StartupSnapshot,
    evaluate_startup_readiness,
)


def _snapshot(*, blocked: bool):
    return evaluate_startup_readiness((
        StartupComponent(
            "memory", schema_revision="memory-v1",
            local_state=ReadinessState.BLOCKED if blocked else ReadinessState.READY,
        ),
        StartupComponent("chat", schema_revision="chat-v1"),
    ))


def test_reflected_temporary_requirement_substitution_cannot_skip_blocked_lane(
    monkeypatch,
):
    snapshot = _snapshot(blocked=True)
    requirement = SyntheticReadinessRequirement("memory", "memory-v1")
    original = StartupSnapshot._assert_integrity
    calls = 0

    def reflected_requirement_swap(self):
        nonlocal calls
        original(self)
        calls += 1
        if calls == 1:
            object.__setattr__(requirement, "component_id", "chat")
            object.__setattr__(requirement, "schema_revision", "chat-v1")
        elif calls == 2:
            object.__setattr__(requirement, "component_id", "memory")
            object.__setattr__(requirement, "schema_revision", "memory-v1")

    monkeypatch.setattr(StartupSnapshot, "_assert_integrity", reflected_requirement_swap)
    with pytest.raises(SyntheticStartupLeaseRejected, match="blocked"):
        review_synthetic_startup_lease(
            snapshot, (requirement,),
            captured_at_ms=10, now_ms=12, max_age_ms=5,
        )


def test_normal_ready_dependency_diagnostic_remains_non_authoritative():
    receipt = review_synthetic_startup_lease(
        _snapshot(blocked=False),
        (SyntheticReadinessRequirement("memory", "memory-v1"),),
        captured_at_ms=10, now_ms=12, max_age_ms=5,
    )
    assert receipt.required_components == ("memory",)
    assert receipt.startup_authorized is False
    assert receipt.dispatch_authorized is False
    assert receipt.notification_authorized is False
