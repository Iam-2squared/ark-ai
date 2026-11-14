"""Synthetic startup lease must reject widened budgets and counterfeit probe slots.

The local probe is untrusted; no READY observation authorizes startup,
external tools, notifications, or hardware access.
"""

from __future__ import annotations

import pytest

from ark import startup_readiness_lease_review as lease
from ark import startup_readiness_review as readiness


def _case():
    snapshot = readiness.evaluate_startup_readiness((
        readiness.StartupComponent("local-core", schema_revision="v1"),
    ))
    requirements = (
        lease.SyntheticReadinessRequirement("local-core", "v1"),
    )
    return snapshot, requirements


def _review(snapshot, requirements):
    return lease.review_synthetic_startup_lease(
        snapshot, requirements,
        captured_at_ms=100, now_ms=110, max_age_ms=20,
    )


@pytest.mark.parametrize("name", ("_MAX", "_LIMIT"))
def test_rebound_lease_budget_is_denied_before_probe_access(monkeypatch, name):
    snapshot, requirements = _case()
    with monkeypatch.context() as patch:
        patch.setattr(lease, name, 10**20)
        with pytest.raises(
            lease.SyntheticStartupLeaseRejected,
            match="startup lease limits or source guard changed",
        ):
            _review(snapshot, requirements)
    assert _review(*_case()).startup_authorized is False


@pytest.mark.parametrize(
    "carrier,slot",
    (
        ("snapshot", "components"),
        ("snapshot", "digest"),
        ("component", "component_id"),
        ("component", "effective_state"),
    ),
)
def test_forged_startup_probe_descriptor_never_reads_private_probe(
    monkeypatch, carrier, slot,
):
    snapshot, requirements = _case()
    observed = []
    cls = (
        readiness.StartupSnapshot
        if carrier == "snapshot" else readiness.ComponentResult
    )

    def hostile(_self):
        observed.append(slot)
        raise AssertionError("unreviewed probe descriptor was invoked")

    with monkeypatch.context() as patch:
        patch.setattr(cls, slot, property(hostile))
        with pytest.raises(
            lease.SyntheticStartupLeaseRejected,
            match="startup lease source descriptor changed",
        ):
            _review(snapshot, requirements)
    assert observed == []


def test_replaced_source_validator_is_denied_without_invocation(monkeypatch):
    snapshot, requirements = _case()
    invoked = []

    def forbidden():
        invoked.append(True)

    with monkeypatch.context() as patch:
        patch.setattr(lease, "_assert_original_startup_constructors", forbidden)
        with pytest.raises(
            lease.SyntheticStartupLeaseRejected,
            match="startup lease limits or source guard changed",
        ):
            _review(snapshot, requirements)
    assert invoked == []


def test_normal_startup_lease_is_diagnostic_only():
    result = _review(*_case())
    assert result.required_components == ("local-core",)
    assert result.captured_at_ms == 100
    assert result.checked_at_ms == 110
    assert result.startup_authorized is False
    assert result.dispatch_authorized is False
    assert result.notification_authorized is False
