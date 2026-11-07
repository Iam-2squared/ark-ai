"""Reject impossible started-child READ recovery histories after restart.

All inputs are fabricated local mock states; classification never dispatches
a Tool, retries unknown effects or treats a supplied digest as evidence.
"""

from __future__ import annotations

import pytest

from ark.agency.disconnected_read_recovery_schedule import (
    DetachedReadRecoveryRejected,
    ReadRecoveryStep,
    schedule_detached_read_recovery,
)

_REQUEST = "req_" + "a" * 32
_PARENT = "step_" + "1" * 16
_CHILD = "step_" + "2" * 16
_DIGEST = "b" * 64


def _step(
    step_id: str, state: str, predecessors: tuple[str, ...] = (),
) -> ReadRecoveryStep:
    return ReadRecoveryStep(
        step_id, "math.sum", predecessors, state,
        _DIGEST if state == "SUCCEEDED" else None,
    )


@pytest.mark.parametrize("ancestor", ("NOT_STARTED", "FAILED", "RUNNING", "UNKNOWN"))
@pytest.mark.parametrize("child", ("FAILED", "RUNNING", "UNKNOWN"))
def test_started_child_with_unresolved_parent_is_rejected(
    ancestor: str, child: str,
) -> None:
    with pytest.raises(DetachedReadRecoveryRejected, match="unresolved dependency"):
        schedule_detached_read_recovery(
            _REQUEST,
            (
                _step(_PARENT, ancestor),
                _step(_CHILD, child, (_PARENT,)),
            ),
        )


@pytest.mark.parametrize("child,expected", (
    ("FAILED", "TERMINAL_FAILURE"),
    ("RUNNING", "QUARANTINE_UNCERTAIN"),
    ("UNKNOWN", "QUARANTINE_UNCERTAIN"),
))
def test_started_child_after_completed_parent_remains_inert(
    child: str, expected: str,
) -> None:
    review = schedule_detached_read_recovery(
        _REQUEST,
        (_step(_PARENT, "SUCCEEDED"), _step(_CHILD, child, (_PARENT,))),
    )
    assert tuple(decision.disposition for decision in review.decisions) == (
        "COMPLETE_UNVERIFIED", expected,
    )
    assert review.dispatch_authorized is False
    assert review.automatic_replay_authorized is False
    assert review.external_outcome_verified is False


@pytest.mark.parametrize("ancestor,expected", (
    ("NOT_STARTED", "WAIT_DEPENDENCY"),
    ("FAILED", "HOLD_FAILED"),
    ("RUNNING", "HOLD_UNCERTAIN"),
    ("UNKNOWN", "HOLD_UNCERTAIN"),
))
def test_unstarted_child_still_reports_safe_holds(
    ancestor: str, expected: str,
) -> None:
    result = schedule_detached_read_recovery(
        _REQUEST,
        (_step(_PARENT, ancestor), _step(_CHILD, "NOT_STARTED", (_PARENT,))),
    )
    assert result.decisions[1].disposition == expected
    assert result.dispatch_authorized is False
