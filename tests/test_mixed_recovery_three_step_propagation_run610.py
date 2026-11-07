"""Three-level and fan-in disconnected Planner recovery safety matrix.

These are local synthetic claims, not real dispatch, authority, consent,
authenticated persisted state, or permission to replay a WRITE occurrence.
"""

import pytest

from ark.agency.disconnected_write_recovery_fence import (
    OfflineRecoveryStepClaim,
    review_disconnected_recovery_fence,
)

PLAN = "plan_" + "a" * 64
A = "step_" + "1" * 16
B = "step_" + "2" * 16
C = "step_" + "3" * 16
HASH = "b" * 64
STATES = (
    "PENDING", "RUNNING", "UNKNOWN", "SUCCEEDED",
    "FAILED", "CANCELLED", "BLOCKED",
)


def _claim(name, effect, state, deps=(), *, reserved=False):
    return OfflineRecoveryStepClaim(
        name, effect, deps, state,
        HASH if state == "SUCCEEDED" else None,
        "slot_" + "e" * 64 if reserved else None,
    )


def _safe(result):
    assert result.dispatch_authorized is False
    assert result.automatic_replay_authorized is False
    assert result.write_authorized is False
    assert result.external_outcome_verified is False


@pytest.mark.parametrize("root_state", STATES)
@pytest.mark.parametrize("root_effect", ("READ", "WRITE"))
@pytest.mark.parametrize("middle_effect", ("READ", "WRITE"))
@pytest.mark.parametrize("leaf_effect", ("READ", "WRITE"))
def test_three_step_pending_descendants_preserve_terminal_and_unknown(
    root_state, root_effect, middle_effect, leaf_effect,
):
    plan = (
        _claim(A, root_effect, root_state),
        _claim(B, middle_effect, "PENDING", (A,)),
        _claim(C, leaf_effect, "PENDING", (B,)),
    )
    review = review_disconnected_recovery_fence(PLAN, plan)
    _safe(review)
    assert review == review_disconnected_recovery_fence(PLAN, plan)
    codes = tuple(item.code for item in review.decisions)
    if root_state in ("FAILED", "CANCELLED", "BLOCKED"):
        assert codes[1:] == ("HOLD_TERMINAL", "HOLD_TERMINAL")
    elif root_state in ("RUNNING", "UNKNOWN"):
        assert codes[1:] == ("HOLD_UNCERTAIN", "HOLD_UNCERTAIN")
    elif root_state == "PENDING":
        assert codes[1:] == ("WAIT_DEPENDENCY", "WAIT_DEPENDENCY")
    else:
        assert codes[1] == (
            "READY_MOCK_ONLY" if middle_effect == "READ"
            else "HELD_WRITE_APPROVAL"
        )
        assert codes[2] == "WAIT_DEPENDENCY"
    if root_effect == "WRITE":
        assert codes[0] != "READY_MOCK_ONLY"
    if leaf_effect == "WRITE":
        assert codes[2] != "READY_MOCK_ONLY"


@pytest.mark.parametrize("root_effect", ("READ", "WRITE"))
@pytest.mark.parametrize("leaf_effect", ("READ", "WRITE"))
def test_reserved_write_root_blocks_multiple_pending_levels(
    root_effect, leaf_effect,
):
    root = _claim(A, root_effect, "PENDING", reserved=root_effect == "WRITE")
    plan = (
        root,
        _claim(B, "READ", "PENDING", (A,)),
        _claim(C, leaf_effect, "PENDING", (B,)),
    )
    review = review_disconnected_recovery_fence(PLAN, plan)
    _safe(review)
    if root_effect == "WRITE":
        assert tuple(d.code for d in review.decisions) == (
            "QUARANTINE_RESERVED_WRITE", "HOLD_UNCERTAIN", "HOLD_UNCERTAIN",
        )
    else:
        assert tuple(d.code for d in review.decisions) == (
            "READY_MOCK_ONLY", "WAIT_DEPENDENCY", "WAIT_DEPENDENCY",
        )


@pytest.mark.parametrize("uncertain_state", ("UNKNOWN", "RUNNING"))
@pytest.mark.parametrize("terminal_state", ("FAILED", "CANCELLED", "BLOCKED"))
@pytest.mark.parametrize("leaf_effect", ("READ", "WRITE"))
def test_fan_in_terminal_outweighs_uncertainty(
    uncertain_state, terminal_state, leaf_effect,
):
    plan = (
        _claim(A, "WRITE", uncertain_state),
        _claim(B, "READ", terminal_state),
        _claim(C, leaf_effect, "PENDING", (A, B)),
    )
    review = review_disconnected_recovery_fence(PLAN, plan)
    _safe(review)
    assert review.decisions[0].code == "QUARANTINE_WRITE_UNKNOWN"
    assert review.decisions[1].code == "TERMINAL"
    assert review.decisions[2].code == "HOLD_TERMINAL"
