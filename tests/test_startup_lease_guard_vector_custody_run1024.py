"""Run1024: startup lease descriptor vectors cannot be rebound to skip checks.

Only synthetic readiness snapshots are used. No startup, backend, notification,
hardware, or external effect is authorized.
"""

from __future__ import annotations

import pytest

import ark.startup_readiness_lease_review as lease
from ark.startup_readiness_review import (
    StartupComponent,
    StartupSnapshot,
    evaluate_startup_readiness,
)

_VECTOR_NAMES = (
    "_REQUIREMENT_FIELDS",
    "_REQUIREMENT_HOOKS",
    "_LEASE_FIELDS",
    "_LEASE_HOOKS",
    "_LEASE_AUTHORITY_FIELDS",
    "_ORIGINAL_REQUIREMENT_FIELDS",
    "_ORIGINAL_REQUIREMENT_HOOKS",
    "_ORIGINAL_LEASE_FIELDS",
    "_ORIGINAL_LEASE_HOOKS",
    "_ORIGINAL_LEASE_AUTHORITY",
)


def _fixture():
    snapshot = evaluate_startup_readiness((
        StartupComponent("memory", schema_revision="memory-v1"),
        StartupComponent("planner", ("memory",), schema_revision="planner-v1"),
    ))
    requirements = (
        lease.SyntheticReadinessRequirement("memory", "memory-v1"),
        lease.SyntheticReadinessRequirement("planner", "planner-v1"),
    )
    return snapshot, requirements


def _review(snapshot, requirements):
    return lease.review_synthetic_startup_lease(
        snapshot, requirements, captured_at_ms=100, now_ms=101,
        max_age_ms=10,
    )


@pytest.mark.parametrize("vector", _VECTOR_NAMES)
@pytest.mark.parametrize("mutation", ("empty", "equal-valued-clone"))
def test_rebound_guard_vectors_rejected_before_snapshot_integrity_callback(
    vector, mutation, monkeypatch,
):
    snapshot, requirements = _fixture()
    original = getattr(lease, vector)
    replacement = (
        () if mutation == "empty" else tuple(list(original))
    )
    if mutation == "equal-valued-clone":
        assert replacement == original
    assert replacement is not original
    callbacks = []

    def forbidden(_self):
        callbacks.append("snapshot integrity")
        raise AssertionError("snapshot integrity must not run before vector admission")

    with monkeypatch.context() as patch:
        patch.setattr(lease, vector, replacement)
        patch.setattr(StartupSnapshot, "_assert_integrity", forbidden)
        with pytest.raises(
            lease.SyntheticStartupLeaseRejected,
            match="startup lease guard vector changed",
        ):
            _review(snapshot, requirements)

    assert callbacks == []


@pytest.mark.parametrize("mutation", ("empty", "equal-valued-clone"))
def test_rebound_guard_vector_root_is_rejected_before_snapshot_callback(
    mutation, monkeypatch,
):
    snapshot, requirements = _fixture()
    original = lease._ORIGINAL_GUARD_VECTOR_REFERENCES
    replacement = (
        () if mutation == "empty" else tuple(list(original))
    )
    if mutation == "equal-valued-clone":
        assert replacement == original
    assert replacement is not original
    callbacks = []

    def forbidden(_self):
        callbacks.append("snapshot integrity")
        raise AssertionError("snapshot integrity must not run before root admission")

    with monkeypatch.context() as patch:
        patch.setattr(lease, "_ORIGINAL_GUARD_VECTOR_REFERENCES", replacement)
        patch.setattr(StartupSnapshot, "_assert_integrity", forbidden)
        with pytest.raises(
            lease.SyntheticStartupLeaseRejected,
            match="startup lease guard-vector reference changed",
        ):
            _review(snapshot, requirements)

    assert callbacks == []


def test_original_startup_lease_remains_diagnostic_only():
    result = _review(*_fixture())
    assert result.required_components == ("memory", "planner")
    assert result.startup_authorized is False
    assert result.dispatch_authorized is False
    assert result.notification_authorized is False
