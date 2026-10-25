"""Exact startup requirement and snapshot carriers remain deny-only fixtures."""

import pytest

import ark.startup_readiness_lease_review as lease
from ark.startup_readiness_review import (
    StartupComponent,
    StartupSnapshot,
    evaluate_startup_readiness,
)


def _state():
    snapshot = evaluate_startup_readiness((
        StartupComponent("memory-long", schema_revision="memory-v1"),
        StartupComponent("planner-long", ("memory-long",), schema_revision="planner-v1"),
    ))
    required = (
        lease.SyntheticReadinessRequirement("memory-long", "memory-v1"),
        lease.SyntheticReadinessRequirement("planner-long", "planner-v1"),
    )
    return snapshot, required


def _review(state):
    snapshot, required = state
    return lease.review_synthetic_startup_lease(
        snapshot, required, captured_at_ms=100, now_ms=101, max_age_ms=2,
    )


@pytest.mark.parametrize("field", ["component_id", "schema_revision"])
def test_requirement_shape_callback_cannot_replace_equal_field_carrier(
    monkeypatch, field,
):
    snapshot, required = _state()
    target = required[0]
    original = getattr(target, field)
    clone = ("!" + original)[1:]
    assert clone == original and clone is not original
    check = lease.SyntheticReadinessRequirement.assert_shape

    def reflected(self):
        check(self)
        if self is target:
            object.__setattr__(self, field, clone)

    monkeypatch.setattr(lease.SyntheticReadinessRequirement, "assert_shape", reflected)
    with pytest.raises(lease.SyntheticStartupLeaseRejected, match="epoch"):
        _review((snapshot, required))


@pytest.mark.parametrize("field", [
    "component_id", "schema_revision", "failure_code",
])
def test_snapshot_integrity_callback_cannot_replace_equal_component_carrier(
    monkeypatch, field,
):
    snapshot, required = _state()
    item = snapshot.components[0]
    original = getattr(item, field)
    if original is None:
        pytest.skip("none is singleton and cannot be copied")
    clone = ("!" + original)[1:]
    assert clone == original and clone is not original
    check = StartupSnapshot._assert_integrity
    calls = 0

    def reflected(self):
        nonlocal calls
        check(self)
        calls += 1
        if calls == 1:
            object.__setattr__(item, field, clone)

    monkeypatch.setattr(StartupSnapshot, "_assert_integrity", reflected)
    with pytest.raises(lease.SyntheticStartupLeaseRejected, match="changed"):
        _review((snapshot, required))


def test_receipt_constructor_cannot_mutate_requirement_after_last_review(
    monkeypatch,
):
    snapshot, required = _state()
    true_constructor = lease.SyntheticStartupLeaseReview

    def reflected_constructor(*args, **kwargs):
        object.__setattr__(required[0], "component_id", "unrecognized")
        return true_constructor(*args, **kwargs)

    monkeypatch.setattr(lease, "SyntheticStartupLeaseReview", reflected_constructor)
    with pytest.raises(lease.SyntheticStartupLeaseRejected, match="epoch"):
        _review((snapshot, required))


def test_valid_readiness_is_content_minimized_and_not_authorization():
    result = _review(_state())
    assert result.required_components == ("memory-long", "planner-long")
    assert result.startup_authorized is False
    assert result.notification_authorized is False
    assert result.dispatch_authorized is False
