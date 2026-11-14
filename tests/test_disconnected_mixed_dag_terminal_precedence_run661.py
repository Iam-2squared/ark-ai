"""A deep disconnected mixed-plan DAG propagates independent stop reasons.

All step states are manually supplied, never verified observations of tools.
No backend, token, clock, approval, network or real action is involved.
"""

from __future__ import annotations

import pytest

from ark.agency.disconnected_write_recovery_fence import (
    OfflineRecoveryFenceRejected,
    OfflineRecoveryStepClaim,
    review_disconnected_recovery_fence,
)

_PLAN = "plan_" + "a" * 64
_IDS = tuple("step_" + f"{i:x}" * 16 for i in range(1, 10))
_A, _B, _C, _D, _E, _F, _G, _H, _I = _IDS
_RESERVED = "slot_" + "f" * 64


@pytest.mark.parametrize("unknown_write", ("RUNNING", "UNKNOWN"))
@pytest.mark.parametrize("terminal_read", ("FAILED", "CANCELLED"))
def test_mixed_deep_dag_propagates_terminal_before_uncertain_without_dispatch(
    unknown_write, terminal_read,
):
    steps = (
        OfflineRecoveryStepClaim(_A, "WRITE", (), unknown_write),
        OfflineRecoveryStepClaim(_B, "READ", (), terminal_read),
        OfflineRecoveryStepClaim(_C, "READ", (_A, _B), "PENDING"),
        OfflineRecoveryStepClaim(_D, "WRITE", (_C,), "PENDING"),
        OfflineRecoveryStepClaim(_E, "READ", (_A,), "PENDING"),
        OfflineRecoveryStepClaim(_F, "READ", (_E,), "PENDING"),
        OfflineRecoveryStepClaim(
            _G, "WRITE", (), "PENDING", reservation_id=_RESERVED,
        ),
        OfflineRecoveryStepClaim(_H, "READ", (_G,), "PENDING"),
        OfflineRecoveryStepClaim(_I, "READ", (), "PENDING"),
    )
    view = review_disconnected_recovery_fence(_PLAN, steps)
    assert tuple((decision.step_id, decision.code) for decision in view.decisions) == (
        (_A, "QUARANTINE_WRITE_UNKNOWN"),
        (_B, "TERMINAL"),
        (_C, "HOLD_TERMINAL"),
        (_D, "HOLD_TERMINAL"),
        (_E, "HOLD_UNCERTAIN"),
        (_F, "HOLD_UNCERTAIN"),
        (_G, "QUARANTINE_RESERVED_WRITE"),
        (_H, "HOLD_UNCERTAIN"),
        (_I, "READY_MOCK_ONLY"),
    )
    assert view == review_disconnected_recovery_fence(_PLAN, steps)
    assert view.dispatch_authorized is False
    assert view.write_authorized is False
    assert view.automatic_replay_authorized is False
    assert view.external_outcome_verified is False


@pytest.mark.parametrize("later_state", ("PENDING", "CANCELLED", "UNKNOWN"))
def test_two_distinct_write_steps_must_not_claim_same_reservation(
    later_state,
):
    steps = (
        OfflineRecoveryStepClaim(
            _A, "WRITE", (), "UNKNOWN", reservation_id=_RESERVED,
        ),
        OfflineRecoveryStepClaim(
            _B, "WRITE", (), later_state, reservation_id=_RESERVED,
        ),
    )
    with pytest.raises(
        OfflineRecoveryFenceRejected, match="reservation reused",
    ):
        review_disconnected_recovery_fence(_PLAN, steps)
