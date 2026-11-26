"""Crash-safe synthetic Planner terminal fanout and sibling recovery.

All tools are inert descriptors; no executor, clock authority, consent,
external effect, or automatic retry is exercised.
"""

from __future__ import annotations

import pytest

from ark.agency.contracts import PlanConflictError, PlanStep, StepState, ToolCall
from ark.agency.planner_journal_review import SyntheticPlanJournal


def _steps():
    def step(name, dependencies=()):
        return PlanStep(
            name,
            ToolCall("fixture", "fixture.read", "sandbox", {"node": name}),
            depends_on=dependencies,
        )

    return (
        step("root"),
        step("child", ("root",)),
        step("leaf", ("child",)),
        step("independent"),
    )


def _statuses(recovery):
    return {name: (state, revision) for name, state, revision in recovery.step_statuses}


@pytest.mark.parametrize("terminal", (StepState.FAILED, StepState.CANCELLED))
def test_recovered_terminal_cascade_cannot_be_replayed_as_ready(
    tmp_path, terminal,
):
    path = tmp_path / "terminal-dag.sqlite"
    writer = SyntheticPlanJournal(path, _steps())
    origin = writer.recover()
    running = writer.append(
        "root", StepState.RUNNING, expected_revision=0,
        at_ms=10, retained=origin.tail,
    )
    terminal_receipt = writer.append(
        "root", terminal, expected_revision=1,
        at_ms=20, retained=running.tail,
    )
    expected = {
        "root": (terminal.value, 2),
        "child": (StepState.BLOCKED.value, 1),
        "leaf": (StepState.BLOCKED.value, 1),
        "independent": (StepState.PENDING.value, 0),
    }
    assert _statuses(terminal_receipt) == expected
    assert terminal_receipt.ambiguous_running_steps == ()
    assert terminal_receipt.dispatch_authorized is False
    assert terminal_receipt.automatic_replay_authorized is False

    cold = SyntheticPlanJournal(path, _steps())
    recovered = cold.recover(retained=running.tail)
    assert recovered.tail == terminal_receipt.tail
    assert _statuses(recovered) == expected
    assert recovered.ambiguous_running_steps == ()
    assert recovered.dispatch_authorized is False
    assert recovered.automatic_replay_authorized is False

    for name, revision in (("root", 0), ("child", 1), ("leaf", 1)):
        with pytest.raises(PlanConflictError):
            cold.append(
                name, StepState.RUNNING, expected_revision=revision,
                at_ms=21, retained=recovered.tail,
            )
        assert cold.recover(retained=running.tail).tail == terminal_receipt.tail

    # An independent sibling is not silently promoted by a failed root,
    # but an explicit synthetic transition is journaled and remains UNKNOWN.
    sibling = cold.append(
        "independent", StepState.RUNNING, expected_revision=0,
        at_ms=30, retained=terminal_receipt.tail,
    )
    cold_again = SyntheticPlanJournal(path, _steps()).recover(
        retained=terminal_receipt.tail,
    )
    assert cold_again.tail == sibling.tail
    assert cold_again.ambiguous_running_steps == ("independent",)
    assert _statuses(cold_again)["child"] == (StepState.BLOCKED.value, 1)
    assert _statuses(cold_again)["leaf"] == (StepState.BLOCKED.value, 1)
    assert cold_again.dispatch_authorized is False
    assert cold_again.automatic_replay_authorized is False
