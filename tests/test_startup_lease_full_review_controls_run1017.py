"""Run1017: full startup lease review rejects diagnostic controls before snapshot integrity."""

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
    ("raw", "message"),
    (
        ("mem\nory", "ASCII control"),
        ("mem\ttory", "ASCII control"),
        ("mem\x7fory", "ASCII control"),
        ("mem\u0085ory", "Unicode formatting control"),
        ("mem\u202eory", "Unicode formatting control"),
        ("mem\u200bory", "Unicode formatting control"),
        ("mem\u2028ory", "Unicode formatting control"),
        ("mem\u2029ory", "Unicode formatting control"),
        ("mem\u00adory", "Unicode formatting control"),
        ("mem\ufeffory", "Unicode formatting control"),
    ),
)
def test_full_review_rejects_control_identity_before_snapshot_integrity(
    field: str, raw: str, message: str,
) -> None:
    snapshot = evaluate_startup_readiness((
        StartupComponent("memory", schema_revision="memory-v1"),
    ))
    # Poison a later snapshot-integrity stage. Requirement admission must
    # reject first, so the diagnostic-control error remains the observed cause.
    object.__setattr__(snapshot, "digest", "startup_corrupted_fixture")
    values = {"component_id": "memory", "schema_revision": "memory-v1"}
    values[field] = raw
    requirement = SyntheticReadinessRequirement(**values)

    with pytest.raises(SyntheticStartupLeaseRejected, match=message):
        review_synthetic_startup_lease(
            snapshot, (requirement,), captured_at_ms=10, now_ms=11,
            max_age_ms=5,
        )


def test_full_review_accepts_ordinary_multilingual_identity_before_snapshot_check():
    snapshot = evaluate_startup_readiness((
        StartupComponent("memory-記録", schema_revision="schema-v1"),
    ))
    requirement = SyntheticReadinessRequirement("memory-記録", "schema-v1")
    result = review_synthetic_startup_lease(
        snapshot, (requirement,), captured_at_ms=10, now_ms=11,
        max_age_ms=5,
    )
    assert result.required_components == ("memory-記録",)
    assert result.startup_authorized is False
    assert result.dispatch_authorized is False
    assert result.notification_authorized is False
