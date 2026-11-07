"""Bounded recovery DAG matrix: disconnected status is never dispatch authority.

This tests only immutable synthetic claims and never invokes a ToolBackend.
"""

import pytest

from ark.agency.disconnected_write_recovery_fence import (
    OfflineRecoveryFenceRejected,
    OfflineRecoveryStepClaim,
    review_disconnected_recovery_fence,
)

PLAN = "plan_" + "a" * 64
A = "step_" + "1" * 16
B = "step_" + "2" * 16
DIGEST = "c" * 64
STATES = (
    "PENDING", "RUNNING", "UNKNOWN", "SUCCEEDED",
    "FAILED", "CANCELLED", "BLOCKED",
)


def _claim(step_id, effect, state, deps=(), reserved=False):
    return OfflineRecoveryStepClaim(
        step_id, effect, deps, state,
        DIGEST if state == "SUCCEEDED" else None,
        "slot_" + "e" * 64 if reserved else None,
    )


@pytest.mark.parametrize("parent_effect", ("READ", "WRITE"))
@pytest.mark.parametrize("child_effect", ("READ", "WRITE"))
@pytest.mark.parametrize("parent_state", STATES)
@pytest.mark.parametrize("child_state", STATES)
def test_two_node_recovery_matrix_never_mints_authority(
    parent_effect, child_effect, parent_state, child_state,
):
    parent = _claim(A, parent_effect, parent_state)
    child = _claim(B, child_effect, child_state, (A,))
    # A started child is invalid unless its prerequisite really completed.
    invalid_start = (
        child_state in ("RUNNING", "SUCCEEDED", "FAILED")
        and parent_state != "SUCCEEDED"
    )
    if invalid_start:
        with pytest.raises(
            OfflineRecoveryFenceRejected, match="prerequisites",
        ):
            review_disconnected_recovery_fence(PLAN, (parent, child))
        return
    first = review_disconnected_recovery_fence(PLAN, (parent, child))
    second = review_disconnected_recovery_fence(PLAN, (parent, child))
    assert first == second
    assert first.digest == second.digest
    assert first.dispatch_authorized is False
    assert first.automatic_replay_authorized is False
    assert first.write_authorized is False
    assert first.external_outcome_verified is False

    for claim, decision in zip((parent, child), first.decisions, strict=True):
        assert decision.step_id == claim.step_id
        if decision.code == "READY_MOCK_ONLY":
            assert claim.effect == "READ"
            assert claim.state == "PENDING"
            assert not claim.depends_on or parent_state == "SUCCEEDED"
        if claim.effect == "WRITE":
            assert decision.code != "READY_MOCK_ONLY"
        if claim.state in ("UNKNOWN", "RUNNING") and claim.effect == "WRITE":
            assert decision.code == "QUARANTINE_WRITE_UNKNOWN"
    if parent_state in ("UNKNOWN", "RUNNING") and child_state == "PENDING":
        assert first.decisions[1].code == "HOLD_UNCERTAIN"
    if parent_state in ("FAILED", "CANCELLED", "BLOCKED") and child_state == "PENDING":
        assert first.decisions[1].code == "HOLD_TERMINAL"


@pytest.mark.parametrize("root_state", ("SUCCEEDED", "FAILED", "UNKNOWN"))
def test_reserved_pending_write_remains_held_even_after_recovery(root_state):
    root = _claim(A, "READ", root_state)
    child = _claim(B, "WRITE", "PENDING", (A,), reserved=True)
    review = review_disconnected_recovery_fence(PLAN, (root, child))
    assert review.decisions[1].code == "QUARANTINE_RESERVED_WRITE"
    assert review.automatic_replay_authorized is False
    assert review.dispatch_authorized is False
