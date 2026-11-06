"""Disconnected Planner restart states stay non-authorizing in a mixed fence.

This test manually transcribes synthetic journal status into detached claims.
It is not an authenticated automatic integration or a real ToolBackend run.
"""

import pytest

from ark.agency.contracts import PlanConflictError, PlanStep, StepState, ToolCall
from ark.agency.disconnected_write_recovery_fence import (
    OfflineRecoveryStepClaim,
    review_disconnected_recovery_fence,
)
from ark.agency.planner_journal_review import SyntheticPlanJournal

PLAN = "plan_" + "a" * 64
WRITE = "step_" + "1" * 16
CHILD = "step_" + "2" * 16
INDEPENDENT = "step_" + "3" * 16
RESULT = "b" * 64
RESERVATION = "slot_" + "c" * 64


def _topology():
    return (
        PlanStep(WRITE, ToolCall("fixture", "offline", "local", {"id": "write"})),
        PlanStep(
            CHILD, ToolCall("fixture", "offline", "local", {"id": "child"}),
            (WRITE,),
        ),
        PlanStep(
            INDEPENDENT, ToolCall("fixture", "offline", "local", {"id": "read"}),
        ),
    )


def _offline_review(recovery, *, write_reserved=False):
    states = {name: state for name, state, _revision in recovery.step_statuses}

    def claim(name, effect, dependencies=()):
        state = states[name].upper()
        # A persisted RUNNING step is conservatively represented as UNKNOWN
        # after restart. Neither this conversion nor a digest is authority.
        if state == "RUNNING":
            state = "UNKNOWN"
        return OfflineRecoveryStepClaim(
            name,
            effect,
            dependencies,
            state,
            RESULT if state == "SUCCEEDED" else None,
            RESERVATION if name == WRITE and write_reserved else None,
        )

    return review_disconnected_recovery_fence(PLAN, (
        claim(WRITE, "WRITE"),
        claim(CHILD, "READ", (WRITE,)),
        claim(INDEPENDENT, "READ"),
    ))


@pytest.mark.parametrize(
    ("ending", "expected"),
    (
        (None, ("QUARANTINE_WRITE_UNKNOWN", "HOLD_UNCERTAIN", "READY_MOCK_ONLY")),
        (StepState.FAILED, ("TERMINAL", "TERMINAL", "READY_MOCK_ONLY")),
        (StepState.CANCELLED, ("TERMINAL", "TERMINAL", "READY_MOCK_ONLY")),
        (StepState.SUCCEEDED, ("COMPLETE_UNVERIFIED", "READY_MOCK_ONLY", "READY_MOCK_ONLY")),
    ),
)
def test_persisted_write_state_does_not_create_restart_permission(
    tmp_path, ending, expected,
):
    path = tmp_path / "planner-fence.sqlite"
    steps = _topology()
    journal = SyntheticPlanJournal(path, steps)
    genesis = journal.recover().tail
    journal.append(
        WRITE, StepState.RUNNING, expected_revision=0,
        at_ms=100, retained=genesis,
    )
    if ending is not None:
        journal.append(
            WRITE, ending, expected_revision=1,
            at_ms=101, retained=genesis,
        )

    reopened = SyntheticPlanJournal(path, steps)
    recovered = reopened.recover(retained=genesis)
    if ending is None:
        assert recovered.ambiguous_running_steps == (WRITE,)
        with pytest.raises(PlanConflictError):
            reopened.append(
                WRITE, StepState.RUNNING, expected_revision=1,
                at_ms=102, retained=genesis,
            )

    fence = _offline_review(recovered)
    assert tuple(x.code for x in fence.decisions) == expected
    assert fence.dispatch_authorized is False
    assert fence.automatic_replay_authorized is False
    assert fence.write_authorized is False
    assert fence.external_outcome_verified is False
    assert reopened.recover(retained=genesis) == recovered


def test_reserved_pending_write_holds_dependent_read_but_not_sibling(tmp_path):
    path = tmp_path / "planner-reserved.sqlite"
    steps = _topology()
    journal = SyntheticPlanJournal(path, steps)
    genesis = journal.recover().tail
    recovered = SyntheticPlanJournal(path, steps).recover(retained=genesis)
    fence = _offline_review(recovered, write_reserved=True)
    assert tuple(x.code for x in fence.decisions) == (
        "QUARANTINE_RESERVED_WRITE",
        "HOLD_UNCERTAIN",
        "READY_MOCK_ONLY",
    )
    assert fence.automatic_replay_authorized is False
    assert journal.recover(retained=genesis) == recovered
