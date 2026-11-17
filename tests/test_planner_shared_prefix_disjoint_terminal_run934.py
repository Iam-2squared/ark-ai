"""Planner retained history is prefix evidence, never step-CAS authority.

Two disconnected handles may append independent branches after a common
genesis. Same-step stale revisions cannot succeed, and a terminal failure
must propagate to a join across a cold restart without any tool dispatch.
"""

from __future__ import annotations

import pytest

from ark.agency.contracts import PlanConflictError, PlanStep, StepState, ToolCall
from ark.agency.planner_journal_review import SyntheticPlanJournal

_CALL = ToolCall("fixture.offline", "fixture.write", "private", {"id": 1})
_STEPS = (
    PlanStep("left", _CALL),
    PlanStep("right", _CALL),
    PlanStep("join", _CALL, ("left", "right")),
)


@pytest.mark.parametrize(
    "right_terminal",
    (StepState.SUCCEEDED, StepState.FAILED, StepState.CANCELLED),
)
def test_independent_prefix_advances_without_laundering_stale_step_cas(
    tmp_path, right_terminal: StepState,
) -> None:
    path = tmp_path / "planner-shared-prefix.sqlite3"
    left_handle = SyntheticPlanJournal(path, _STEPS)
    genesis = left_handle.recover().tail
    right_handle = SyntheticPlanJournal(path, _STEPS)
    left_running = left_handle.append(
        "left", StepState.RUNNING, expected_revision=0,
        at_ms=1, retained=genesis,
    )
    # The right handle has not seen the new tip. A valid old prefix plus an
    # independent revision still permits a safe local state-only append.
    right_running = right_handle.append(
        "right", StepState.RUNNING, expected_revision=0,
        at_ms=2, retained=genesis,
    )
    assert right_running.tail.event_count == 2

    with pytest.raises(PlanConflictError):
        right_handle.append(
            "left", StepState.RUNNING, expected_revision=0,
            at_ms=3, retained=genesis,
        )
    assert left_handle.recover().tail == right_running.tail

    left_done = left_handle.append(
        "left", StepState.SUCCEEDED, expected_revision=1,
        at_ms=3, retained=left_running.tail,
    )
    right_done = right_handle.append(
        "right", right_terminal, expected_revision=1,
        at_ms=4, retained=genesis,
    )
    assert left_done.tail.event_count == 3
    assert right_done.tail.event_count == 4
    cold = SyntheticPlanJournal(path, _STEPS)
    recovered = cold.recover(retained=genesis)
    states = {
        name: (state, revision)
        for name, state, revision in recovered.step_statuses
    }
    assert states["left"] == ("succeeded", 2)
    assert states["right"] == (right_terminal.value, 2)
    assert recovered.ambiguous_running_steps == ()
    assert recovered.dispatch_authorized is False
    assert recovered.automatic_replay_authorized is False

    if right_terminal is StepState.SUCCEEDED:
        assert states["join"] == ("pending", 0)
        started = cold.append(
            "join", StepState.RUNNING, expected_revision=0,
            at_ms=5, retained=genesis,
        )
        assert started.tail.event_count == 5
        assert started.dispatch_authorized is False
    else:
        assert states["join"] == ("blocked", 1)
        with pytest.raises(PlanConflictError):
            cold.append(
                "join", StepState.RUNNING, expected_revision=1,
                at_ms=5, retained=genesis,
            )
        assert cold.recover().tail == recovered.tail
