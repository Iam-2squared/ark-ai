"""Startup lease must retain its import-original guard helpers.

All probes are synthetic and deny-only. These tests do not activate startup,
dispatch, notifications, credentials, hardware, or a real backend.
"""

from __future__ import annotations

import pytest

import ark.startup_readiness_lease_review as mod
from ark.startup_readiness_review import (
    ReadinessState,
    StartupComponent,
    evaluate_startup_readiness,
)


@pytest.fixture
def ready_case():
    snapshot = evaluate_startup_readiness((
        StartupComponent("conversation", schema_revision="v1"),
        StartupComponent("memory", schema_revision="v1"),
    ))
    requirements = (mod.SyntheticReadinessRequirement("memory", "v1"),)
    return snapshot, requirements


def _review(snapshot, requirements, **clock):
    values = {
        "captured_at_ms": 100,
        "now_ms": 110,
        "max_age_ms": 10,
    }
    values.update(clock)
    return mod.review_synthetic_startup_lease(
        snapshot, requirements, **values,
    )


def test_fresh_exact_component_lease_remains_diagnostic_only(ready_case):
    snapshot, requirements = ready_case

    result = _review(snapshot, requirements)

    assert result.snapshot_digest == snapshot.digest
    assert result.required_components == ("memory",)
    assert result.captured_at_ms == 100
    assert result.checked_at_ms == 110
    assert result.startup_authorized is False
    assert result.dispatch_authorized is False
    assert result.notification_authorized is False


def test_unrelated_blocked_component_does_not_poison_required_ready_lane():
    snapshot = evaluate_startup_readiness((
        StartupComponent(
            "conversation",
            local_state=ReadinessState.BLOCKED,
            failure_code="conversation_probe_failed",
        ),
        StartupComponent("memory", schema_revision="v1"),
    ))
    requirements = (mod.SyntheticReadinessRequirement("memory", "v1"),)

    result = _review(snapshot, requirements)

    assert result.required_components == ("memory",)
    assert result.startup_authorized is False


def test_required_blocked_component_is_rejected():
    snapshot = evaluate_startup_readiness((
        StartupComponent(
            "memory",
            local_state=ReadinessState.BLOCKED,
            failure_code="memory_probe_failed",
            schema_revision="v1",
        ),
    ))
    requirements = (mod.SyntheticReadinessRequirement("memory", "v1"),)

    with pytest.raises(mod.SyntheticStartupLeaseRejected, match="blocked"):
        _review(snapshot, requirements)


def test_schema_mismatch_and_duplicate_requirements_are_rejected(ready_case):
    snapshot, requirements = ready_case

    with pytest.raises(mod.SyntheticStartupLeaseRejected, match="schema-stale"):
        _review(
            snapshot,
            (mod.SyntheticReadinessRequirement("memory", "v2"),),
        )
    with pytest.raises(mod.SyntheticStartupLeaseRejected, match="duplicate"):
        _review(snapshot, (requirements[0], requirements[0]))


@pytest.mark.parametrize(
    ("clock", "message"),
    (
        ({"max_age_ms": 9}, "expired"),
        ({"captured_at_ms": 111, "now_ms": 110}, "expired"),
        ({"captured_at_ms": -1}, "expired"),
    ),
)
def test_stale_or_regressing_lease_clock_is_rejected(ready_case, clock, message):
    snapshot, requirements = ready_case

    with pytest.raises(mod.SyntheticStartupLeaseRejected, match=message):
        _review(snapshot, requirements, **clock)


@pytest.mark.parametrize(
    ("helper_name", "carrier", "field", "collapse_vectors"),
    (
        (
            "_require_original_requirement",
            mod._REQUIREMENT_TYPE,
            "component_id",
            False,
        ),
        (
            "_require_original_lease_result",
            mod._LEASE_TYPE,
            "dispatch_authorized",
            False,
        ),
        (
            "_require_original_lease_protocol",
            mod._REQUIREMENT_TYPE,
            "component_id",
            True,
        ),
    ),
)
def test_replaced_guard_helper_is_denied_before_descriptor_callback(
    ready_case, monkeypatch, helper_name, carrier, field, collapse_vectors,
):
    snapshot, requirements = ready_case
    callbacks = []

    def forbidden(_self):
        callbacks.append(field)
        raise AssertionError("unreviewed startup lease descriptor was invoked")

    # Replacing a guard with a no-op used to make the corresponding class
    # descriptor inventory replaceable or empty without an early denial.
    monkeypatch.setattr(mod, helper_name, lambda: None)
    if collapse_vectors:
        monkeypatch.setattr(mod, "_REQUIREMENT_FIELDS", ())
        monkeypatch.setattr(mod, "_ORIGINAL_REQUIREMENT_FIELDS", ())
    monkeypatch.setattr(carrier, field, property(forbidden))

    with pytest.raises(
        mod.SyntheticStartupLeaseRejected, match="helper identity",
    ):
        _review(snapshot, requirements)

    assert callbacks == []


def test_replaced_integrity_method_denied_before_lease_guard_callback(
    ready_case, monkeypatch,
):
    snapshot, requirements = ready_case
    original = mod.StartupSnapshot._assert_integrity
    observed = []

    def reentrant_integrity(self):
        original(self)
        if not observed:
            observed.append("snapshot-integrity")
            monkeypatch.setattr(
                mod, "_require_original_lease_result", lambda: None,
            )

    monkeypatch.setattr(
        mod.StartupSnapshot, "_assert_integrity", reentrant_integrity,
    )

    with pytest.raises(
        mod.SyntheticStartupLeaseRejected, match="startup lease source descriptor changed",
    ):
        _review(snapshot, requirements)

    assert observed == []


def test_replaced_guard_tuple_is_denied_before_helper_or_descriptor_use(
    ready_case, monkeypatch,
):
    snapshot, requirements = ready_case
    callbacks = []

    def forbidden(_self):
        callbacks.append("requirement")
        raise AssertionError("unreviewed requirement descriptor was invoked")

    monkeypatch.setattr(
        mod,
        "_ORIGINAL_LEASE_GUARD_HELPERS",
        tuple(list(mod._ORIGINAL_LEASE_GUARD_HELPERS)),
    )
    monkeypatch.setattr(
        mod._REQUIREMENT_TYPE, "component_id", property(forbidden),
    )

    with pytest.raises(
        mod.SyntheticStartupLeaseRejected, match="helper identity",
    ):
        _review(snapshot, requirements)

    assert callbacks == []
