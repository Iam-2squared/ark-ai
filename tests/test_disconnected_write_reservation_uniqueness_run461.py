"""Duplicate untrusted WRITE reservation identity must fail closed before recovery."""

from __future__ import annotations

import pytest

from ark.agency.disconnected_write_recovery_fence import (
    OfflineRecoveryFenceRejected,
    OfflineRecoveryStepClaim,
    review_disconnected_recovery_fence,
)

_PLAN = "plan_" + "a" * 64
_A = "step_" + "1" * 16
_B = "step_" + "2" * 16
_C = "step_" + "3" * 16
_SLOT = "slot_" + "b" * 64
_OTHER_SLOT = "slot_" + "c" * 64
_SUCCESS = "d" * 64


def _step(name, state="PENDING", reservation=None, deps=(), result=None):
    return OfflineRecoveryStepClaim(name, "WRITE", deps, state, result, reservation)


@pytest.mark.parametrize("states", [
    ("PENDING", "PENDING"),
    ("UNKNOWN", "PENDING"),
    ("RUNNING", "UNKNOWN"),
    ("FAILED", "CANCELLED"),
    ("SUCCEEDED", "PENDING"),
])
def test_reused_reservation_rejected_across_write_states(states):
    first, second = states
    result = _SUCCESS if first == "SUCCEEDED" else None
    steps = (_step(_A, first, _SLOT, result=result), _step(_B, second, _SLOT))
    with pytest.raises(OfflineRecoveryFenceRejected, match="reservation reused"):
        review_disconnected_recovery_fence(_PLAN, steps)


def test_distinct_reservations_are_independently_quarantined():
    review = review_disconnected_recovery_fence(
        _PLAN, (_step(_A, reservation=_SLOT), _step(_B, reservation=_OTHER_SLOT)),
    )
    assert tuple(r.code for r in review.decisions) == (
        "QUARANTINE_RESERVED_WRITE", "QUARANTINE_RESERVED_WRITE",
    )
    assert not review.dispatch_authorized
    assert not review.automatic_replay_authorized


def test_reuse_is_rejected_even_with_dependency():
    with pytest.raises(OfflineRecoveryFenceRejected, match="reservation reused"):
        review_disconnected_recovery_fence(
            _PLAN, (_step(_A, "SUCCEEDED", _SLOT, result=_SUCCESS),
                    _step(_B, reservation=_SLOT, deps=(_A,))),
        )


def test_unreserved_write_behavior_unchanged():
    review = review_disconnected_recovery_fence(
        _PLAN, (_step(_A), _step(_B, reservation=_SLOT),
                OfflineRecoveryStepClaim(_C, "READ", (), "PENDING")),
    )
    assert tuple(x.code for x in review.decisions) == (
        "HELD_WRITE_APPROVAL", "QUARANTINE_RESERVED_WRITE", "READY_MOCK_ONLY",
    )
