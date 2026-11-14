"""Planner's durable diamond restart projects to a non-authorizing mixed fence.

All statuses are manually transcribed from LOCAL synthetic SQLite fixtures.
No actual tool backend, PermissionGate token, or authenticated approval is used.
"""

from __future__ import annotations

import pytest

from ark.agency.contracts import (
    PlanConflictError,
    PlanStep,
    StepState,
    ToolCall,
)
from ark.agency.disconnected_write_recovery_fence import (
    OfflineRecoveryStepClaim,
    review_disconnected_recovery_fence,
)
from ark.agency.planner_journal_review import SyntheticPlanJournal

_PLAN_ID = "plan_" + "9" * 64
_A = "step_" + "1" * 16
_B = "step_" + "2" * 16
_JOIN = "step_" + "3" * 16
_INDEPENDENT = "step_" + "4" * 16


def _topology():
    return (
        PlanStep(_A, ToolCall("fixture", "offline", "local", {"name": "a"})),
        PlanStep(_B, ToolCall("fixture", "offline", "local", {"name": "b"})),
        PlanStep(
            _JOIN, ToolCall("fixture", "offline", "local", {"name": "join"}),
            (_A, _B),
        ),
        PlanStep(
            _INDEPENDENT,
            ToolCall("fixture", "offline", "local", {"name": "independent"}),
        ),
    )


def _fence(recovered):
    states = {name: state for name, state, _rev in recovered.step_statuses}
    claims = []
    for step_id, effect, dependencies in (
        (_A, "WRITE", ()),
        (_B, "READ", ()),
        (_JOIN, "WRITE", (_A, _B)),
        (_INDEPENDENT, "READ", ()),
    ):
        persisted = states[step_id].upper()
        state = "UNKNOWN" if persisted == "RUNNING" else persisted
        claims.append(OfflineRecoveryStepClaim(
            step_id, effect, dependencies, state,
            "f" * 64 if state == "SUCCEEDED" else None,
        ))
    result = review_disconnected_recovery_fence(_PLAN_ID, tuple(claims))
    assert result.dispatch_authorized is False
    assert result.write_authorized is False
    assert result.automatic_replay_authorized is False
    assert result.external_outcome_verified is False
    return tuple(item.code for item in result.decisions)


@pytest.mark.parametrize("ending", (StepState.FAILED, StepState.CANCELLED))
def test_write_root_terminal_survives_other_root_completion(
    tmp_path, ending,
):
    path = tmp_path / "mixed-diamond.sqlite"
    steps = _topology()
    a, b = SyntheticPlanJournal(path, steps), SyntheticPlanJournal(path, steps)
    genesis = a.recover().tail

    a.append(_A, StepState.RUNNING, expected_revision=0, at_ms=10, retained=genesis)
    b.append(_B, StepState.RUNNING, expected_revision=0, at_ms=11, retained=genesis)
    a.append(_A, ending, expected_revision=1, at_ms=12, retained=genesis)
    b.append(_B, StepState.SUCCEEDED, expected_revision=1, at_ms=13, retained=genesis)

    fresh = SyntheticPlanJournal(path, steps)
    recovered = fresh.recover(retained=genesis)
    assert recovered.ambiguous_running_steps == ()
    assert dict((n, s) for n, s, _ in recovered.step_statuses)[_JOIN] == "blocked"
    assert _fence(recovered) == (
        "TERMINAL", "COMPLETE_UNVERIFIED", "TERMINAL", "READY_MOCK_ONLY",
    )
    assert fresh.recover(retained=genesis) == recovered
    with pytest.raises(PlanConflictError):
        fresh.append(
            _JOIN, StepState.RUNNING, expected_revision=0,
            at_ms=14, retained=genesis,
        )
    assert fresh.recover(retained=genesis) == recovered


def test_two_ambiguous_roots_hold_join_but_not_independent_mock_read(tmp_path):
    path = tmp_path / "two-running-roots.sqlite"
    steps = _topology()
    a, b = SyntheticPlanJournal(path, steps), SyntheticPlanJournal(path, steps)
    genesis = a.recover().tail

    a.append(_A, StepState.RUNNING, expected_revision=0, at_ms=10, retained=genesis)
    b.append(_B, StepState.RUNNING, expected_revision=0, at_ms=11, retained=genesis)

    fresh = SyntheticPlanJournal(path, steps)
    recovered = fresh.recover(retained=genesis)
    assert recovered.ambiguous_running_steps == (_A, _B)
    assert _fence(recovered) == (
        "QUARANTINE_WRITE_UNKNOWN", "QUARANTINE_UNKNOWN",
        "HOLD_UNCERTAIN", "READY_MOCK_ONLY",
    )
    for step_id in (_A, _B):
        with pytest.raises(PlanConflictError):
            fresh.append(
                step_id, StepState.RUNNING, expected_revision=1,
                at_ms=12, retained=genesis,
            )
    assert fresh.recover(retained=genesis) == recovered
