"""Independent disconnected READ recovery diamond/terminal propagation cases.

All states and digests are synthetic. READY_MOCK_ONLY never implies a real
ToolRegistry dispatch, consent, external verification or automatic replay.
"""

from __future__ import annotations

import pytest

from ark.agency.disconnected_read_recovery_schedule import (
    DetachedReadRecoveryRejected,
    ReadRecoveryStep,
    schedule_detached_read_recovery,
)

_REQUEST = "req_" + "a" * 32
_A = "step_" + "1" * 16
_B = "step_" + "2" * 16
_C = "step_" + "3" * 16
_D = "step_" + "4" * 16
_E = "step_" + "5" * 16


def _row(name, state, dependencies=()):
    return ReadRecoveryStep(
        name, "math.sum", dependencies, state,
        "b" * 64 if state == "SUCCEEDED" else None,
    )


@pytest.mark.parametrize(("root_state", "root_code", "join_code", "tail_code"), (
    ("NOT_STARTED", "READY_MOCK_ONLY", "WAIT_DEPENDENCY", "WAIT_DEPENDENCY"),
    ("SUCCEEDED", "COMPLETE_UNVERIFIED", "READY_MOCK_ONLY", "WAIT_DEPENDENCY"),
    ("FAILED", "TERMINAL_FAILURE", "HOLD_FAILED", "HOLD_FAILED"),
    ("RUNNING", "QUARANTINE_UNCERTAIN", "HOLD_UNCERTAIN", "HOLD_UNCERTAIN"),
    ("UNKNOWN", "QUARANTINE_UNCERTAIN", "HOLD_UNCERTAIN", "HOLD_UNCERTAIN"),
))
def test_diamond_pending_join_is_not_replayed_through_uncertain_root(
    root_state, root_code, join_code, tail_code,
):
    graph = (
        _row(_A, root_state),
        _row(_B, "SUCCEEDED"),
        _row(_C, "NOT_STARTED", (_A, _B)),
        _row(_D, "NOT_STARTED", (_C,)),
        _row(_E, "NOT_STARTED"),
    )
    report = schedule_detached_read_recovery(_REQUEST, graph)
    expected = {
        _A: root_code,
        _B: "COMPLETE_UNVERIFIED",
        _C: join_code,
        _D: tail_code,
        _E: "READY_MOCK_ONLY",
    }
    assert {row.step_id: row.disposition for row in report.decisions} == expected
    assert len(report.schedule_digest) == 64
    assert report == schedule_detached_read_recovery(_REQUEST, graph)
    assert report.dispatch_authorized is False
    assert report.automatic_replay_authorized is False
    assert report.external_outcome_verified is False


@pytest.mark.parametrize("unresolved", (
    "NOT_STARTED", "FAILED", "RUNNING", "UNKNOWN",
))
@pytest.mark.parametrize("impossible_child_state", (
    "SUCCEEDED", "FAILED", "RUNNING", "UNKNOWN",
))
def test_started_child_cannot_follow_unresolved_parent(
    unresolved, impossible_child_state,
):
    graph = (
        _row(_A, unresolved),
        _row(_B, impossible_child_state, (_A,)),
    )
    with pytest.raises(
        DetachedReadRecoveryRejected,
        match="after unresolved dependency",
    ):
        schedule_detached_read_recovery(_REQUEST, graph)


@pytest.mark.parametrize("root_state", ("FAILED", "RUNNING", "UNKNOWN"))
def test_failed_and_ambiguous_siblings_never_grant_mock_execution(root_state):
    graph = (
        _row(_A, root_state),
        _row(_B, "NOT_STARTED", (_A,)),
        _row(_C, "NOT_STARTED", (_B,)),
    )
    report = schedule_detached_read_recovery(_REQUEST, graph)
    codes = {row.step_id: row.disposition for row in report.decisions}
    blocking = "HOLD_FAILED" if root_state == "FAILED" else "HOLD_UNCERTAIN"
    assert codes[_B] == blocking
    assert codes[_C] == blocking
    assert report.dispatch_authorized is False
