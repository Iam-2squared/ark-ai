"""Mixed synthetic recovery remains non-authorizing across independent waves.

No registry, backend, action clock, database, or permission issuer participates.
These claims are intentionally untrusted fixture labels, not recovered effects.
"""

from __future__ import annotations

import pytest

from ark.agency.disconnected_write_recovery_fence import (
    OfflineRecoveryFenceRejected,
    OfflineRecoveryStepClaim,
    review_disconnected_recovery_fence,
)

PLAN = "plan_" + "f" * 64
A = "step_" + "a" * 16
B = "step_" + "b" * 16
C = "step_" + "c" * 16
D = "step_" + "d" * 16
E = "step_" + "e" * 16
RESERVATION = "slot_" + "7" * 64


def claim(name, effect, state="PENDING", deps=(), *, result=None, reservation=None):
    return OfflineRecoveryStepClaim(
        name, effect, deps, state, result, reservation,
    )


def decisions(*steps):
    report = review_disconnected_recovery_fence(PLAN, steps)
    assert report.dispatch_authorized is False
    assert report.automatic_replay_authorized is False
    assert report.write_authorized is False
    assert report.external_outcome_verified is False
    return {item.step_id: item.code for item in report.decisions}


@pytest.mark.parametrize("read_state", ("RUNNING", "UNKNOWN"))
@pytest.mark.parametrize("write_state", ("RUNNING", "UNKNOWN"))
def test_two_disconnected_uncertain_roots_only_hold_their_own_descendants(
    read_state, write_state,
):
    codes = decisions(
        claim(A, "READ", read_state),
        claim(B, "WRITE", write_state),
        claim(C, "READ", deps=(A,)),
        claim(D, "WRITE", deps=(B,)),
        claim(E, "READ"),
    )
    assert codes == {
        A: "QUARANTINE_UNKNOWN",
        B: "QUARANTINE_WRITE_UNKNOWN",
        C: "HOLD_UNCERTAIN",
        D: "HOLD_UNCERTAIN",
        E: "READY_MOCK_ONLY",
    }


@pytest.mark.parametrize("terminal", ("FAILED", "CANCELLED", "BLOCKED"))
def test_terminal_ancestor_takes_priority_over_separate_unknown_ancestor(terminal):
    codes = decisions(
        claim(A, "READ", terminal),
        claim(B, "WRITE", "UNKNOWN"),
        claim(C, "READ", deps=(A, B)),
        claim(D, "WRITE"),
    )
    assert codes == {
        A: "TERMINAL",
        B: "QUARANTINE_WRITE_UNKNOWN",
        C: "HOLD_TERMINAL",
        D: "HELD_WRITE_APPROVAL",
    }


def test_reserved_pending_write_holds_descendants_without_freezing_unrelated_read():
    codes = decisions(
        claim(A, "WRITE", reservation=RESERVATION),
        claim(B, "READ", deps=(A,)),
        claim(C, "READ"),
    )
    assert codes == {
        A: "QUARANTINE_RESERVED_WRITE",
        B: "HOLD_UNCERTAIN",
        C: "READY_MOCK_ONLY",
    }


def test_duplicate_reservation_between_independent_writes_is_rejected():
    with pytest.raises(
        OfflineRecoveryFenceRejected, match="reservation reused",
    ):
        decisions(
            claim(A, "WRITE", reservation=RESERVATION),
            claim(B, "WRITE", reservation=RESERVATION),
        )


@pytest.mark.parametrize("active", ("RUNNING", "FAILED", "SUCCEEDED"))
def test_active_step_cannot_follow_an_uncompleted_prerequisite(active):
    result = "1" * 64 if active == "SUCCEEDED" else None
    with pytest.raises(
        OfflineRecoveryFenceRejected, match="before prerequisites",
    ):
        decisions(
            claim(A, "READ", "UNKNOWN"),
            claim(B, "READ", active, (A,), result=result),
        )


def test_claimed_success_hash_is_unverified_and_never_approval():
    codes = decisions(
        claim(A, "READ", "SUCCEEDED", result="a" * 64),
        claim(B, "WRITE", deps=(A,)),
        claim(C, "READ", deps=(A,)),
    )
    assert codes == {
        A: "COMPLETE_UNVERIFIED",
        B: "HELD_WRITE_APPROVAL",
        C: "READY_MOCK_ONLY",
    }
