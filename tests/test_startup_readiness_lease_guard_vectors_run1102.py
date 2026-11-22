"""Run1102: startup lease guard vectors and denial descriptors stay pinned.

Synthetic-only. These tests never open a device/store or grant startup,
notification, dispatch, human-consent or backend authority.
"""

from __future__ import annotations

import pytest

import ark.startup_readiness_lease_review as lease
from ark.startup_readiness_review import (
    StartupComponent,
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
    "_ORIGINAL_GUARD_VECTOR_REFERENCES",
)


def _inputs():
    snapshot = evaluate_startup_readiness((
        StartupComponent("memory", schema_revision="memory-v1"),
        StartupComponent(
            "planner", ("memory",), schema_revision="planner-v1",
        ),
    ))
    requirements = (
        lease.SyntheticReadinessRequirement("planner", "planner-v1"),
        lease.SyntheticReadinessRequirement("memory", "memory-v1"),
    )
    return snapshot, requirements


def _review(snapshot, requirements, **changes):
    values = {
        "captured_at_ms": 100,
        "now_ms": 105,
        "max_age_ms": 10,
    }
    values.update(changes)
    return lease.review_synthetic_startup_lease(
        snapshot, requirements, **values,
    )


@pytest.mark.parametrize("vector", _VECTOR_NAMES)
@pytest.mark.parametrize("replacement", ("empty", "equal-valued-clone"))
def test_guard_vector_rebinding_fails_before_requirement_access(
    monkeypatch, vector, replacement,
):
    snapshot, requirements = _inputs()
    accessed = []

    def poison(_self):
        accessed.append(True)
        raise AssertionError("unreviewed requirement field was read")

    original = getattr(lease, vector)
    replacement_value = (
        () if replacement == "empty" else tuple(list(original))
    )
    assert replacement_value is not original

    monkeypatch.setattr(
        lease.SyntheticReadinessRequirement,
        "component_id",
        property(poison),
    )
    monkeypatch.setattr(lease, vector, replacement_value)

    with pytest.raises(lease.SyntheticStartupLeaseRejected, match="guard.vector"):
        _review(snapshot, requirements)

    assert accessed == []


def test_requirement_descriptor_replacement_fails_before_snapshot_review(monkeypatch):
    snapshot, requirements = _inputs()
    accessed = []

    def poison(_self):
        accessed.append(True)
        raise AssertionError("unreviewed requirement descriptor was invoked")

    monkeypatch.setattr(
        lease.SyntheticReadinessRequirement,
        "component_id",
        property(poison),
    )

    with pytest.raises(
        lease.SyntheticStartupLeaseRejected,
        match="requirement descriptor changed",
    ):
        _review(snapshot, requirements)

    assert accessed == []


def test_lease_authority_descriptor_replacement_fails_before_receipt_read(
    monkeypatch,
):
    snapshot, requirements = _inputs()
    accessed = []

    def poison(_self):
        accessed.append(True)
        raise AssertionError("unreviewed authority descriptor was invoked")

    monkeypatch.setattr(
        lease.SyntheticStartupLeaseReview,
        "startup_authorized",
        property(poison),
    )

    with pytest.raises(
        lease.SyntheticStartupLeaseRejected,
        match="authority epoch changed",
    ):
        _review(snapshot, requirements)

    assert accessed == []


@pytest.mark.parametrize("field", ("component_id", "schema_revision"))
@pytest.mark.parametrize(
    "bad_value",
    (
        "memory\x00",
        "memory\n",
        "memory\u0085",
        "memory\u202e",
        "memory\u200b",
        "\ud800",
        "é" * 129,
    ),
)
def test_requirement_text_rejects_controls_invalid_utf8_and_byte_overflow(
    field, bad_value,
):
    snapshot, _ = _inputs()
    values = {"component_id": "memory", "schema_revision": "memory-v1"}
    values[field] = bad_value
    requirement = lease.SyntheticReadinessRequirement(**values)

    with pytest.raises(lease.SyntheticStartupLeaseRejected, match="invalid"):
        _review(snapshot, (requirement,))


def test_requirement_count_is_bounded_before_component_matching():
    snapshot, _ = _inputs()
    requirements = tuple(
        lease.SyntheticReadinessRequirement("memory", "memory-v1")
        for _ in range(513)
    )

    with pytest.raises(
        lease.SyntheticStartupLeaseRejected,
        match="exact synthetic lease inputs",
    ):
        _review(snapshot, requirements)


def test_maximum_age_is_an_exact_bounded_integer():
    snapshot, requirements = _inputs()

    with pytest.raises(
        lease.SyntheticStartupLeaseRejected,
        match="expired or clock regressed",
    ):
        _review(snapshot, requirements, max_age_ms=2**63)
