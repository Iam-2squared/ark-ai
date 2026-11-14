"""FAILED restart claims require completed prerequisites, not inferred execution.

The disconnected recovery fence never authorizes mock or real tool effects.
FAILED is a started terminal claim; BLOCKED/CANCELLED can be unstarted.
"""

from __future__ import annotations

import pytest

from ark.agency.disconnected_write_recovery_fence import (
    OfflineRecoveryFenceRejected,
    OfflineRecoveryStepClaim,
    review_disconnected_recovery_fence,
)

PLAN = "plan_" + "b" * 64
A = "step_" + "1" * 16
B = "step_" + "2" * 16
C = "step_" + "3" * 16
SHA = "d" * 64


@pytest.mark.parametrize("effect", ("READ", "WRITE"))
@pytest.mark.parametrize("ancestor", ("PENDING", "RUNNING", "UNKNOWN", "FAILED"))
def test_failed_descendant_cannot_claim_execution_before_ancestor_success(
    ancestor, effect,
):
    steps = (
        OfflineRecoveryStepClaim(A, "READ", (), ancestor),
        OfflineRecoveryStepClaim(B, effect, (A,), "FAILED"),
    )
    with pytest.raises(OfflineRecoveryFenceRejected, match="prerequisites"):
        review_disconnected_recovery_fence(PLAN, steps)


@pytest.mark.parametrize("child", ("BLOCKED", "CANCELLED", "PENDING"))
def test_unstarted_descendant_is_held_after_failed_ancestor(child):
    steps = (
        OfflineRecoveryStepClaim(A, "READ", (), "FAILED"),
        OfflineRecoveryStepClaim(B, "WRITE", (A,), child),
    )
    report = review_disconnected_recovery_fence(PLAN, steps)
    assert report.decisions[1].code in ("TERMINAL", "HOLD_TERMINAL")
    assert report.write_authorized is False
    assert report.automatic_replay_authorized is False


def test_failed_started_child_after_success_is_terminal_but_not_authority():
    steps = (
        OfflineRecoveryStepClaim(A, "READ", (), "SUCCEEDED", SHA),
        OfflineRecoveryStepClaim(B, "WRITE", (A,), "FAILED"),
        OfflineRecoveryStepClaim(C, "READ", (B,), "PENDING"),
    )
    result = review_disconnected_recovery_fence(PLAN, steps)
    assert tuple(row.code for row in result.decisions) == (
        "COMPLETE_UNVERIFIED", "TERMINAL", "HOLD_TERMINAL",
    )
    assert result.dispatch_authorized is False
    assert result.external_outcome_verified is False
