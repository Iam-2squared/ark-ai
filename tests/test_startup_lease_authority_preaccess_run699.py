"""Synthetic startup receipts reject replaced authority getters before probes.

A False-returning fixture property may still execute or leak local probe
metadata. A READY synthetic diagnostic cannot enable real startup or dispatch.
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
    StartupComponent,
    StartupSnapshot,
    evaluate_startup_readiness,
)


def _fixture():
    snapshot = evaluate_startup_readiness((
        StartupComponent("memory", schema_revision="memory-v1"),
        StartupComponent("planner", ("memory",), schema_revision="planner-v1"),
    ))
    requirements = (
        SyntheticReadinessRequirement("memory", "memory-v1"),
        SyntheticReadinessRequirement("planner", "planner-v1"),
    )
    return snapshot, requirements


def _review(snapshot, requirements):
    return review_synthetic_startup_lease(
        snapshot, requirements, captured_at_ms=100, now_ms=101,
        max_age_ms=10,
    )


@pytest.mark.parametrize("getter", (
    "startup_authorized", "dispatch_authorized", "notification_authorized",
))
@pytest.mark.parametrize("denied", (False, True), ids=("forged-false", "forged-true"))
def test_preinstalled_getter_rejected_without_callback_or_probe(
    monkeypatch, getter, denied,
):
    snapshot, requirements = _fixture()
    callbacks = []
    probes = []

    def forged_getter(_result):
        callbacks.append("unexpected getter execution")
        return denied

    def forbidden_integrity(_snapshot):
        probes.append("unexpected private probe validation")
        pytest.fail("substituted authority getter reached synthetic probe")

    monkeypatch.setattr(
        SyntheticStartupLeaseReview, getter, property(forged_getter),
    )
    monkeypatch.setattr(StartupSnapshot, "_assert_integrity", forbidden_integrity)
    with pytest.raises(SyntheticStartupLeaseRejected, match="authority epoch"):
        _review(snapshot, requirements)
    assert callbacks == []
    assert probes == []


@pytest.mark.parametrize("getter", (
    "startup_authorized", "dispatch_authorized", "notification_authorized",
))
def test_late_getter_substitution_denied_before_getter_dispatch(monkeypatch, getter):
    snapshot, requirements = _fixture()
    original_integrity = StartupSnapshot._assert_integrity
    callbacks = []
    injections = []

    def forged_false(_result):
        callbacks.append("unexpected getter execution")
        return False

    def late_injection(current):
        original_integrity(current)
        if not injections:
            injections.append("installed")
            monkeypatch.setattr(
                SyntheticStartupLeaseReview, getter, property(forged_false),
            )

    monkeypatch.setattr(StartupSnapshot, "_assert_integrity", late_injection)
    with pytest.raises(SyntheticStartupLeaseRejected, match="authority epoch"):
        _review(snapshot, requirements)
    assert injections == ["installed"]
    assert callbacks == []


def test_original_receipt_remains_diagnostic_only():
    snapshot, requirements = _fixture()
    result = _review(snapshot, requirements)
    assert result.required_components == ("memory", "planner")
    assert result.startup_authorized is False
    assert result.dispatch_authorized is False
    assert result.notification_authorized is False
