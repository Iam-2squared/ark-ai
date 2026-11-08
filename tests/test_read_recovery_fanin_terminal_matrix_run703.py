"""Multi-parent READ restart classifications are hints, never dispatch authority.

All histories are synthetic, result digests are supplied rather than authenticated,
and no backend, network, user data or real planner execution is involved.
"""

import pytest

from ark.agency.disconnected_read_recovery_schedule import (
    DetachedReadRecoveryRejected,
    ReadRecoveryStep,
    schedule_detached_read_recovery,
)

REQUEST = "req_" + "e" * 32
IDS = tuple("step_" + char * 16 for char in "abcde")
DIGEST = "f" * 64


def _step(index, state="NOT_STARTED", parents=()):
    return ReadRecoveryStep(
        IDS[index], "math.sum", tuple(IDS[parent] for parent in parents),
        state, DIGEST if state == "SUCCEEDED" else None,
    )


def _schedule(*steps):
    return schedule_detached_read_recovery(REQUEST, tuple(steps))


@pytest.mark.parametrize(
    "root_state,expected_root,expected_join,expected_tail",
    (
        ("NOT_STARTED", "READY_MOCK_ONLY", "WAIT_DEPENDENCY", "WAIT_DEPENDENCY"),
        ("FAILED", "TERMINAL_FAILURE", "HOLD_FAILED", "HOLD_FAILED"),
        ("RUNNING", "QUARANTINE_UNCERTAIN", "HOLD_UNCERTAIN", "HOLD_UNCERTAIN"),
        ("UNKNOWN", "QUARANTINE_UNCERTAIN", "HOLD_UNCERTAIN", "HOLD_UNCERTAIN"),
        ("SUCCEEDED", "COMPLETE_UNVERIFIED", "READY_MOCK_ONLY", "WAIT_DEPENDENCY"),
    ),
)
def test_two_parent_fanin_recovery_and_independent_sibling(
    root_state, expected_root, expected_join, expected_tail,
):
    schedule = _schedule(
        _step(0, "SUCCEEDED"),
        _step(1, root_state),
        _step(2, parents=(0, 1)),
        _step(3, parents=(2,)),
        _step(4),
    )
    assert tuple(item.disposition for item in schedule.decisions) == (
        "COMPLETE_UNVERIFIED", expected_root, expected_join,
        expected_tail, "READY_MOCK_ONLY",
    )
    assert schedule.dispatch_authorized is False
    assert schedule.automatic_replay_authorized is False
    assert schedule.external_outcome_verified is False
    assert len(schedule.schedule_digest) == 64


@pytest.mark.parametrize("uncertain", ("RUNNING", "UNKNOWN"))
def test_terminal_failure_dominates_uncertain_branch_at_fanin(uncertain):
    schedule = _schedule(
        _step(0, "FAILED"),
        _step(1, uncertain),
        _step(2, parents=(0, 1)),
        _step(3, parents=(2,)),
    )
    assert tuple(item.disposition for item in schedule.decisions) == (
        "TERMINAL_FAILURE", "QUARANTINE_UNCERTAIN",
        "HOLD_FAILED", "HOLD_FAILED",
    )
    assert schedule.automatic_replay_authorized is False


@pytest.mark.parametrize("unresolved", ("NOT_STARTED", "FAILED", "RUNNING", "UNKNOWN"))
@pytest.mark.parametrize("started", ("FAILED", "RUNNING", "UNKNOWN"))
def test_started_join_after_unresolved_parent_is_contradictory(
    unresolved, started,
):
    with pytest.raises(
        DetachedReadRecoveryRejected, match="started READ after unresolved dependency",
    ):
        _schedule(
            _step(0, "SUCCEEDED"),
            _step(1, unresolved),
            _step(2, started, parents=(0, 1)),
        )


def test_fanin_success_is_unverified_even_with_all_digest_carriers():
    schedule = _schedule(
        _step(0, "SUCCEEDED"),
        _step(1, "SUCCEEDED"),
        _step(2, "SUCCEEDED", parents=(0, 1)),
        _step(3, "SUCCEEDED", parents=(2,)),
    )
    assert all(
        item.disposition == "COMPLETE_UNVERIFIED"
        for item in schedule.decisions
    )
    assert schedule.dispatch_authorized is False
    assert schedule.automatic_replay_authorized is False
    assert schedule.external_outcome_verified is False
