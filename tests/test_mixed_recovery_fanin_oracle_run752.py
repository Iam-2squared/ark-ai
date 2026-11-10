"""Independent-wave/fan-in recovery oracle for disconnected mixed DAGs.

These are synthetic facts with no durable approval, backend or clock. The
invariant is that a failed or ambiguous ancestor never becomes mock-ready
through another completed branch, and an unrelated READ remains independent.
"""

from __future__ import annotations

import pytest

from ark.agency.disconnected_write_recovery_fence import (
    OfflineRecoveryStepClaim,
    review_disconnected_recovery_fence,
)

_PLAN = "plan_" + "a" * 64
_A = "step_" + "1" * 16
_B = "step_" + "2" * 16
_C = "step_" + "3" * 16
_D = "step_" + "4" * 16
_E = "step_" + "5" * 16
_STATES = (
    "PENDING", "RUNNING", "UNKNOWN", "FAILED",
    "CANCELLED", "BLOCKED", "SUCCEEDED",
)
_TERMINAL = frozenset(("FAILED", "CANCELLED", "BLOCKED"))
_UNCERTAIN = frozenset(("RUNNING", "UNKNOWN"))


def _step(name, effect="READ", state="PENDING", deps=()):
    return OfflineRecoveryStepClaim(
        name, effect, deps, state,
        "e" * 64 if state == "SUCCEEDED" else None,
    )


@pytest.mark.parametrize("write_root_state", _STATES)
@pytest.mark.parametrize("read_root_state", _STATES)
def test_fanin_blocker_precedence_and_disjoint_read_independence(
    write_root_state, read_root_state,
):
    steps = (
        _step(_A, "WRITE", write_root_state),
        _step(_B, "READ", read_root_state),
        _step(_C, "READ", deps=(_A, _B)),
        _step(_D, "READ"),
        _step(_E, "WRITE", deps=(_C,)),
    )
    view = review_disconnected_recovery_fence(_PLAN, steps)
    codes = {decision.step_id: decision.code for decision in view.decisions}
    if {write_root_state, read_root_state} & _TERMINAL:
        assert codes[_C] == "HOLD_TERMINAL"
        assert codes[_E] == "HOLD_TERMINAL"
    elif {write_root_state, read_root_state} & _UNCERTAIN:
        assert codes[_C] == "HOLD_UNCERTAIN"
        assert codes[_E] == "HOLD_UNCERTAIN"
    elif write_root_state == read_root_state == "SUCCEEDED":
        assert codes[_C] == "READY_MOCK_ONLY"
        assert codes[_E] == "WAIT_DEPENDENCY"
    else:
        assert codes[_C] == "WAIT_DEPENDENCY"
        assert codes[_E] == "WAIT_DEPENDENCY"
    assert codes[_D] == "READY_MOCK_ONLY"
    assert codes[_A] != "READY_MOCK_ONLY"
    assert view.dispatch_authorized is False
    assert view.write_authorized is False
    assert view.automatic_replay_authorized is False
    assert view.external_outcome_verified is False
    assert view == review_disconnected_recovery_fence(_PLAN, steps)


@pytest.mark.parametrize("read_root_state", _STATES)
def test_fanin_still_blocks_with_completed_write_parent_and_nonready_read(
    read_root_state,
):
    view = review_disconnected_recovery_fence(
        _PLAN,
        (
            _step(_A, "WRITE", "SUCCEEDED"),
            _step(_B, "READ", read_root_state),
            _step(_C, "READ", deps=(_A, _B)),
        ),
    )
    code = view.decisions[-1].code
    if read_root_state in _TERMINAL:
        assert code == "HOLD_TERMINAL"
    elif read_root_state in _UNCERTAIN:
        assert code == "HOLD_UNCERTAIN"
    elif read_root_state == "SUCCEEDED":
        assert code == "READY_MOCK_ONLY"
    else:
        assert code == "WAIT_DEPENDENCY"
    assert view.external_outcome_verified is False
