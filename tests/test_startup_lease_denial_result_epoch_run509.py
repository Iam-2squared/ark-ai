"""Synthetic READY leases cannot inherit authority from result getters."""

import pytest

from ark.startup_readiness_lease_review import (
    SyntheticReadinessRequirement,
    SyntheticStartupLeaseRejected,
    SyntheticStartupLeaseReview,
    review_synthetic_startup_lease,
)
from ark.startup_readiness_review import (
    StartupComponent,
    evaluate_startup_readiness,
)


def _state():
    snapshot = evaluate_startup_readiness((
        StartupComponent("memory", schema_revision="memory-v1"),
        StartupComponent("planner", ("memory",), schema_revision="planner-v1"),
    ))
    requirements = (
        SyntheticReadinessRequirement("memory", "memory-v1"),
        SyntheticReadinessRequirement("planner", "planner-v1"),
    )
    return snapshot, requirements


def _review(state):
    snapshot, requirements = state
    return review_synthetic_startup_lease(
        snapshot, requirements, captured_at_ms=10, now_ms=11, max_age_ms=2,
    )


def test_unmodified_synthetic_lease_is_never_activation():
    result = _review(_state())
    assert result.required_components == ("memory", "planner")
    assert result.startup_authorized is False
    assert result.dispatch_authorized is False
    assert result.notification_authorized is False


@pytest.mark.parametrize("flag", (
    "startup_authorized", "dispatch_authorized", "notification_authorized",
))
def test_forged_result_authority_property_is_denied(monkeypatch, flag):
    monkeypatch.setattr(
        SyntheticStartupLeaseReview, flag,
        property(lambda self: True),
    )
    with pytest.raises(SyntheticStartupLeaseRejected, match="authority"):
        _review(_state())


@pytest.mark.parametrize("mutation", (
    "requirement", "snapshot", "result_digest", "same_value_components",
))
def test_false_notification_getter_cannot_change_lease_epoch(
    monkeypatch, mutation,
):
    snapshot, requirements = _state()

    def false_with_side_effect(report):
        if mutation == "requirement":
            object.__setattr__(requirements[0], "schema_revision", "unreviewed")
        elif mutation == "snapshot":
            object.__setattr__(snapshot, "digest", "startup_" + "0" * 64)
        elif mutation == "result_digest":
            object.__setattr__(report, "snapshot_digest", "startup_" + "0" * 64)
        else:
            cloned = tuple(list(report.required_components))
            assert cloned == report.required_components
            assert cloned is not report.required_components
            object.__setattr__(report, "required_components", cloned)
        return False

    monkeypatch.setattr(
        SyntheticStartupLeaseReview, "notification_authorized",
        property(false_with_side_effect),
    )
    with pytest.raises(SyntheticStartupLeaseRejected, match="epoch"):
        _review((snapshot, requirements))
