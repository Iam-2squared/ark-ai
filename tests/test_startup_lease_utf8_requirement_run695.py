"""Startup lease cannot reinterpret noncanonical UTF-8 probe identities.

This independent fixture lease remains diagnostic only: a READY snapshot
is not external readiness, human consent, backend dispatch, or notification.
"""

from __future__ import annotations

import pytest

from ark.startup_readiness_lease_review import (
    SyntheticReadinessRequirement,
    SyntheticStartupLeaseRejected,
    review_synthetic_startup_lease,
)
from ark.startup_readiness_review import (
    StartupComponent,
    evaluate_startup_readiness,
)


@pytest.mark.parametrize("field", ("component_id", "schema_revision"))
@pytest.mark.parametrize(
    "invalid",
    ("é" * 129, "😀" * 65, "bad\ud800", "bad\udfff"),
    ids=("two-byte-overflow", "four-byte-overflow", "high-surrogate", "low-surrogate"),
)
def test_invalid_utf8_requirement_rejected_before_snapshot_lookup(field, invalid):
    snapshot = evaluate_startup_readiness((
        StartupComponent("memory", schema_revision="memory-v1"),
    ))
    required = SyntheticReadinessRequirement("memory", "memory-v1")
    object.__setattr__(required, field, invalid)
    with pytest.raises(SyntheticStartupLeaseRejected, match="UTF-8"):
        required.assert_shape()
    with pytest.raises(SyntheticStartupLeaseRejected, match="UTF-8"):
        review_synthetic_startup_lease(
            snapshot, (required,), captured_at_ms=10, now_ms=11,
            max_age_ms=5,
        )


@pytest.mark.parametrize(
    "identity",
    ("a" * 256, "あ" * 85 + "a", "😀" * 64),
    ids=("ascii-256", "mixed-256", "emoji-256"),
)
def test_valid_exact_256_byte_requirement_stays_inert(identity):
    snapshot = evaluate_startup_readiness((
        StartupComponent(identity, schema_revision=identity),
    ))
    requirement = SyntheticReadinessRequirement(identity, identity)
    result = review_synthetic_startup_lease(
        snapshot, (requirement,), captured_at_ms=10, now_ms=11,
        max_age_ms=5,
    )
    assert result.required_components == (identity,)
    assert result.startup_authorized is False
    assert result.dispatch_authorized is False
    assert result.notification_authorized is False
