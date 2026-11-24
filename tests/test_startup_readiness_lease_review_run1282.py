"""Run1282: exercise the disconnected synthetic startup readiness lease.

Only synthetic StartupComponent snapshots are reviewed. The lease is a
diagnostic, never startup, dispatch, notification, trusted-clock or consent
authority.
"""

from __future__ import annotations

import pytest

from ark.startup_readiness_lease_review import (
    SyntheticReadinessRequirement,
    SyntheticStartupLeaseRejected,
    SyntheticStartupLeaseReview,
    review_synthetic_startup_lease,
)
from ark.startup_readiness_review import (
    ReadinessState,
    StartupComponent,
    evaluate_startup_readiness,
)


def _ready_snapshot():
    return evaluate_startup_readiness((
        StartupComponent("memory", schema_revision="memory-v1"),
        StartupComponent(
            "planner",
            dependencies=("memory",),
            schema_revision="planner-v1",
        ),
    ))


def _requirements():
    return (
        SyntheticReadinessRequirement("memory", "memory-v1"),
        SyntheticReadinessRequirement("planner", "planner-v1"),
    )


def _review(snapshot=None, requirements=None, **overrides):
    values = {
        "captured_at_ms": 100,
        "now_ms": 110,
        "max_age_ms": 10,
    }
    values.update(overrides)
    return review_synthetic_startup_lease(
        _ready_snapshot() if snapshot is None else snapshot,
        _requirements() if requirements is None else requirements,
        **values,
    )


def test_fresh_lease_accepts_exact_age_boundary_and_denies_authority():
    snapshot = _ready_snapshot()
    result = _review(snapshot)

    assert type(result) is SyntheticStartupLeaseReview
    assert result.snapshot_digest == snapshot.digest
    assert result.required_components == ("memory", "planner")
    assert result.captured_at_ms == 100
    assert result.checked_at_ms == 110
    assert result.startup_authorized is False
    assert result.dispatch_authorized is False
    assert result.notification_authorized is False


@pytest.mark.parametrize(
    ("now_ms", "max_age_ms"),
    (
        (111, 10),
        (99, 10),
        (100, -1),
        (2**63, 0),
    ),
)
def test_expired_rollback_or_out_of_range_lease_is_rejected(now_ms, max_age_ms):
    with pytest.raises(SyntheticStartupLeaseRejected, match="expired or clock regressed"):
        _review(now_ms=now_ms, max_age_ms=max_age_ms)


@pytest.mark.parametrize(
    "overrides",
    (
        {"captured_at_ms": True},
        {"now_ms": False},
        {"max_age_ms": True},
        {"captured_at_ms": 101, "now_ms": 100},
        {"captured_at_ms": -1},
    ),
)
def test_lease_clock_requires_exact_nonnegative_integer_epoch(overrides):
    with pytest.raises(SyntheticStartupLeaseRejected, match="exact synthetic lease inputs"):
        _review(**overrides)


def test_requirements_must_be_exact_tuple_and_exact_carriers():
    with pytest.raises(SyntheticStartupLeaseRejected, match="exact synthetic lease inputs"):
        _review(requirements=list(_requirements()))

    class RequirementAlias(SyntheticReadinessRequirement):
        pass

    with pytest.raises(SyntheticStartupLeaseRejected, match="exact synthetic lease inputs"):
        _review(requirements=(RequirementAlias("memory", "memory-v1"),))


def test_duplicate_or_missing_required_component_is_rejected():
    duplicate = (
        SyntheticReadinessRequirement("memory", "memory-v1"),
        SyntheticReadinessRequirement("memory", "memory-v1"),
    )
    with pytest.raises(SyntheticStartupLeaseRejected, match="duplicate required"):
        _review(requirements=duplicate)

    missing = (SyntheticReadinessRequirement("voice", "voice-v1"),)
    with pytest.raises(SyntheticStartupLeaseRejected, match="not present"):
        _review(requirements=missing)


def test_blocked_dependency_cannot_be_hidden_by_ready_descendant():
    snapshot = evaluate_startup_readiness((
        StartupComponent(
            "memory",
            local_state=ReadinessState.BLOCKED,
            failure_code="storage-unavailable",
            schema_revision="memory-v1",
        ),
        StartupComponent(
            "planner",
            dependencies=("memory",),
            schema_revision="planner-v1",
        ),
    ))
    with pytest.raises(SyntheticStartupLeaseRejected, match="blocked, degraded"):
        _review(snapshot)


def test_requirement_schema_must_match_current_component():
    wrong = (
        SyntheticReadinessRequirement("memory", "memory-v0"),
        SyntheticReadinessRequirement("planner", "planner-v1"),
    )
    with pytest.raises(SyntheticStartupLeaseRejected, match="schema-stale"):
        _review(requirements=wrong)


def test_reflected_snapshot_mutation_is_rejected_before_lease_return():
    snapshot = _ready_snapshot()
    object.__setattr__(snapshot.components[0], "schema_revision", "forged-v1")
    with pytest.raises(SyntheticStartupLeaseRejected, match="integrity rejected"):
        _review(snapshot)


def test_replaced_requirement_validator_is_denied_before_callback(
    monkeypatch: pytest.MonkeyPatch,
):
    calls = []

    def forged(_self):
        calls.append("called")

    monkeypatch.setattr(SyntheticReadinessRequirement, "assert_shape", forged)
    with pytest.raises(SyntheticStartupLeaseRejected, match="descriptor changed"):
        _review()
    assert calls == []


def test_replaced_result_authority_descriptor_is_denied_before_return(
    monkeypatch: pytest.MonkeyPatch,
):
    calls = []

    def forged(_self):
        calls.append("called")
        return False

    monkeypatch.setattr(
        SyntheticStartupLeaseReview,
        "dispatch_authorized",
        property(forged),
    )
    with pytest.raises(SyntheticStartupLeaseRejected, match="result constructor or descriptor changed"):
        _review()
    assert calls == []
