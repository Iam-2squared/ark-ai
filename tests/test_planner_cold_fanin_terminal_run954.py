"""Durable fan-in terminal state cannot be revived by an independent success.

Synthetic SQLite journal only. No backend execution, authorization, or replay.
"""

import pytest

from ark.agency import PlanConflictError, PlanStep, StepState, ToolCall
from ark.agency.planner_journal_review import (
    SyntheticPlanJournal,
    SyntheticPlanJournalRejected,
)


def _steps() -> tuple[PlanStep, ...]:
    call = ToolCall("synthetic.read", "synthetic.read", "offline")
    return (
        PlanStep("alpha", call),
        PlanStep("beta", call),
        PlanStep("join", call, ("alpha", "beta")),
        PlanStep("child", call, ("join",)),
        PlanStep("unrelated", call),
    )


def _statuses(recovered) -> dict[str, tuple[str, int]]:
    return {step: (state, revision) for step, state, revision in recovered.step_statuses}


@pytest.mark.parametrize("terminal", (StepState.FAILED, StepState.CANCELLED))
@pytest.mark.parametrize("failed_root", ("alpha", "beta"))
def test_cold_fanin_denies_revival_after_other_root_success(
    tmp_path, terminal: StepState, failed_root: str,
) -> None:
    path = tmp_path / "synthetic-plan-fanin.sqlite3"
    original = SyntheticPlanJournal(path, _steps())
    genesis = original.recover().tail
    healthy_root = "beta" if failed_root == "alpha" else "alpha"

    original.append(
        failed_root, StepState.RUNNING, expected_revision=0,
        at_ms=100, retained=genesis,
    )
    after_failure = original.append(
        failed_root, terminal, expected_revision=1,
        at_ms=101, retained=genesis,
    )
    assert _statuses(after_failure)["join"] == ("blocked", 1)
    assert _statuses(after_failure)["child"] == ("blocked", 1)
    assert _statuses(after_failure)[healthy_root] == ("pending", 0)

    # Reopening across the terminal boundary must not promote a blocked fan-in.
    cold = SyntheticPlanJournal(path, _steps())
    before_success = cold.recover(retained=genesis)
    assert _statuses(before_success)["join"] == ("blocked", 1)
    cold.append(
        healthy_root, StepState.RUNNING, expected_revision=0,
        at_ms=102, retained=genesis,
    )
    after_success = cold.append(
        healthy_root, StepState.SUCCEEDED, expected_revision=1,
        at_ms=103, retained=genesis,
    )
    statuses = _statuses(after_success)
    assert statuses[failed_root] == (terminal.value, 2)
    assert statuses[healthy_root] == ("succeeded", 2)
    assert statuses["join"] == ("blocked", 1)
    assert statuses["child"] == ("blocked", 1)
    assert statuses["unrelated"] == ("pending", 0)
    assert after_success.tail.event_count == 4
    assert after_success.dispatch_authorized is False
    assert after_success.automatic_replay_authorized is False

    # A bogus old revision or even a current blocked revision grants no replay.
    with pytest.raises((PlanConflictError, SyntheticPlanJournalRejected)):
        cold.append(
            "join", StepState.RUNNING, expected_revision=1,
            at_ms=104, retained=genesis,
        )
    with pytest.raises((PlanConflictError, SyntheticPlanJournalRejected)):
        cold.append(
            failed_root, StepState.RUNNING, expected_revision=0,
            at_ms=105, retained=genesis,
        )

    checked = SyntheticPlanJournal(path, _steps()).recover(retained=genesis)
    assert checked.tail == after_success.tail
    assert _statuses(checked) == statuses
    assert checked.ambiguous_running_steps == ()
    assert checked.dispatch_authorized is False
    assert checked.automatic_replay_authorized is False
