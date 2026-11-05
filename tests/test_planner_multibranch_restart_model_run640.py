"""Durable multi-branch plan restart must preserve terminal propagation.

This synthetic journal has no ToolBackend, authorization, or automatic retry.
All SQLite files are disposable pytest tmp_path artifacts.
"""

import pytest

from ark.agency.contracts import PlanConflictError, PlanStep, StepState, ToolCall
from ark.agency.planner_journal_review import SyntheticPlanJournal


def _steps():
    return (
        PlanStep("root_a", ToolCall("fixture", "offline", "local", {"n": 1})),
        PlanStep(
            "child_a", ToolCall("fixture", "offline", "local", {"n": 2}),
            ("root_a",),
        ),
        PlanStep(
            "leaf_a", ToolCall("fixture", "offline", "local", {"n": 3}),
            ("child_a",),
        ),
        PlanStep("root_b", ToolCall("fixture", "offline", "local", {"n": 4})),
        PlanStep(
            "child_b", ToolCall("fixture", "offline", "local", {"n": 5}),
            ("root_b",),
        ),
    )


@pytest.mark.parametrize("terminal", [StepState.FAILED, StepState.CANCELLED])
def test_restarts_preserve_independent_branches_and_ambiguous_running(
    tmp_path, terminal,
):
    path = tmp_path / "plan-restart.sqlite"
    steps = _steps()
    journal = SyntheticPlanJournal(path, steps)
    sequence = (
        ("root_a", StepState.RUNNING, 0, 10),
        ("root_b", StepState.RUNNING, 0, 11),
        ("root_a", terminal, 1, 12),
        ("root_b", StepState.SUCCEEDED, 1, 13),
        ("child_b", StepState.RUNNING, 0, 14),
        ("child_b", StepState.SUCCEEDED, 1, 15),
    )
    previous = journal.recover()
    retained_prefix = None

    for ordinal, (step_id, next_state, revision, at_ms) in enumerate(sequence, 1):
        snapshot = journal.append(
            step_id, next_state, expected_revision=revision, at_ms=at_ms,
        )
        assert snapshot.tail.event_count == ordinal
        assert snapshot.tail.last_at_ms == at_ms
        assert snapshot.dispatch_authorized is False
        assert snapshot.automatic_replay_authorized is False
        # Simulate a new process by constructing a new journal object and
        # comparing with the saved receipt after every durable append.
        journal = SyntheticPlanJournal(path, steps)
        restarted = journal.recover(retained=previous.tail)
        assert restarted == snapshot
        previous = restarted
        if ordinal == 3:
            retained_prefix = snapshot.tail
            assert set(snapshot.ambiguous_running_steps) == {"root_b"}
            states = {name: (state, rev) for name, state, rev in snapshot.step_statuses}
            assert states["root_a"] == (terminal.value, 2)
            assert states["child_a"] == ("blocked", 1)
            assert states["leaf_a"] == ("blocked", 1)
            assert states["root_b"] == ("running", 1)

    assert retained_prefix is not None
    assert previous.ambiguous_running_steps == ()
    states = {name: (state, rev) for name, state, rev in previous.step_statuses}
    assert states["root_a"] == (terminal.value, 2)
    assert states["child_a"] == ("blocked", 1)
    assert states["leaf_a"] == ("blocked", 1)
    assert states["root_b"] == ("succeeded", 2)
    assert states["child_b"] == ("succeeded", 2)
    assert SyntheticPlanJournal(path, steps).recover(retained=retained_prefix) == previous

    # Neither a completed step nor a BLOCKED descendant can be dispatched.
    with pytest.raises(PlanConflictError):
        journal.append("child_a", StepState.RUNNING, expected_revision=1, at_ms=16)
    with pytest.raises(PlanConflictError):
        journal.append("child_b", StepState.RUNNING, expected_revision=0, at_ms=16)
    assert journal.recover() == previous
