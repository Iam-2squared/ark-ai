"""Bound mixed-plan offline recovery metadata BEFORE regex or serialization.

Synthetic only: no real device, backend, approval, trusted clock or retry.
"""

from __future__ import annotations

from dataclasses import replace

import pytest

from ark.agency.disconnected_write_recovery_fence import (
    OfflineRecoveryFenceRejected,
    OfflineRecoveryStepClaim,
    review_disconnected_recovery_fence,
)

PLAN = "plan_" + "a" * 64
STEP = "step_" + "1" * 16
STEP2 = "step_" + "2" * 16
SHA = "f" * 64
SLOT = "slot_" + "c" * 64


@pytest.mark.parametrize(
    ("field", "bad"),
    [
        ("step_id", "step_" + "1" * 100_000),
        ("step_id", "step_" + "\ud800" * 100),
        ("effect", "READ" + "X" * 100_000),
        ("depends_on", ("step_" + "1" * 100_000,)),
        ("state", "UNKNOWN" + "X" * 100_000),
        ("result_sha256", "f" * 100_000),
        ("reservation_id", "slot_" + "c" * 100_000),
    ],
)
def test_unbounded_step_fields_fail_without_authority(field, bad):
    valid = OfflineRecoveryStepClaim(STEP, "WRITE", (), "SUCCEEDED", SHA, SLOT)
    forged = replace(valid, **{field: bad})
    with pytest.raises(OfflineRecoveryFenceRejected, match="invalid ordered mixed-plan"):
        review_disconnected_recovery_fence(PLAN, (forged,))


@pytest.mark.parametrize("plan", (
    "plan_" + "a" * 100_000,
    "plan_" + "\ud800" * 100,
))
def test_unbounded_plan_id_refused_before_any_digest(plan):
    with pytest.raises(OfflineRecoveryFenceRejected, match="invalid exact mixed-plan"):
        review_disconnected_recovery_fence(
            plan, (OfflineRecoveryStepClaim(STEP, "READ", (), "PENDING"),),
        )


def test_canonical_bounded_recovery_is_still_deny_only():
    report = review_disconnected_recovery_fence(PLAN, (
        OfflineRecoveryStepClaim(STEP, "WRITE", (), "UNKNOWN", None, SLOT),
        OfflineRecoveryStepClaim(STEP2, "READ", (STEP,), "PENDING"),
    ))
    assert tuple(x.code for x in report.decisions) == (
        "QUARANTINE_WRITE_UNKNOWN", "HOLD_UNCERTAIN",
    )
    assert report.write_authorized is False
    assert report.automatic_replay_authorized is False
    assert report.external_outcome_verified is False
    assert report.dispatch_authorized is False
