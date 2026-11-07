"""Independent Planner SQLite handles never win the same step revision.

The synthetic journal records exact local terminal state, not a real tool
outcome, action consent, or a restart authorization to replay RUNNING.
"""

from __future__ import annotations

import pytest

from ark.agency.contracts import (
    PlanConflictError,
    PlanStep,
    StepState,
    ToolCall,
)
from ark.agency.planner_journal_review import SyntheticPlanJournal

A = "step_" + "a" * 16
B = "step_" + "b" * 16


@pytest.mark.parametrize(
    "terminal",
    (StepState.SUCCEEDED, StepState.FAILED),
)
@pytest.mark.parametrize("collision", ("duplicate_running", "late_terminal"))
def test_separate_writers_cannot_commit_two_transitions_for_one_revision(
    tmp_path, terminal, collision,
):
    steps = (
        PlanStep(A, ToolCall(
            "math.sum", "math.sum", "local-private", {"values": [1, 2]},
        )),
        PlanStep(B, ToolCall(
            "math.sum", "math.sum", "local-private", {"values": [3, 4]},
        ), (A,)),
    )
    path = tmp_path / "planner.sqlite"
    first = SyntheticPlanJournal(path, steps)
    second = SyntheticPlanJournal(path, steps)
    genesis = first.recover().tail
    assert second.recover(retained=genesis).tail == genesis
    started = first.append(
        A, StepState.RUNNING,
        expected_revision=0, at_ms=1, retained=genesis,
    )
    assert started.tail.event_count == 1

    if collision == "duplicate_running":
        with pytest.raises(PlanConflictError):
            second.append(
                A, StepState.RUNNING,
                expected_revision=0, at_ms=2, retained=genesis,
            )
        assert first.recover(retained=genesis) == started
        completed = first.append(
            A, terminal, expected_revision=1, at_ms=3,
            retained=genesis,
        )
    else:
        completed = second.append(
            A, terminal, expected_revision=1, at_ms=2,
            retained=genesis,
        )
        opposite = (
            StepState.FAILED if terminal is StepState.SUCCEEDED
            else StepState.SUCCEEDED
        )
        with pytest.raises(PlanConflictError):
            first.append(
                A, opposite, expected_revision=1, at_ms=3,
                retained=genesis,
            )

    assert completed.tail.event_count == 2
    for reader in (
        first, second, SyntheticPlanJournal(path, steps),
    ):
        recovered = reader.recover(retained=genesis)
        assert recovered == completed
        statuses = {
            step_id: (state, revision)
            for step_id, state, revision in recovered.step_statuses
        }
        assert statuses[A] == (terminal.value, 2)
        assert statuses[B] == (
            ("pending", 0) if terminal is StepState.SUCCEEDED
            else ("blocked", 1)
        )
        assert recovered.ambiguous_running_steps == ()
        assert recovered.dispatch_authorized is False
        assert recovered.automatic_replay_authorized is False
