"""Run950: interleaved Planner roots never erase step revision CAS.

Only synthetic, locally journaled state transitions are tested. Neither
a prior-prefix witness nor RUNNING state authorizes tool execution or replay.
"""

from __future__ import annotations

import sqlite3

import pytest

from ark.agency import PlanConflictError, PlanStep, StepState, ToolCall
from ark.agency.planner_journal_review import (
    SyntheticPlanJournal,
    SyntheticPlanJournalRejected,
)


def _steps() -> tuple[PlanStep, ...]:
    read = ToolCall("synthetic.read", "synthetic.read", "local-only")
    return (PlanStep("alpha", read), PlanStep("beta", read))


@pytest.mark.parametrize("first_id", ("alpha", "beta"))
@pytest.mark.parametrize("terminal", (
    StepState.SUCCEEDED, StepState.FAILED, StepState.CANCELLED,
))
def test_old_prefix_does_not_override_individual_revision_after_interleave(
    tmp_path, first_id: str, terminal: StepState,
) -> None:
    path = tmp_path / "synthetic-interleaved-planner.sqlite3"
    second_id = "beta" if first_id == "alpha" else "alpha"
    initial = SyntheticPlanJournal(path, _steps())
    genesis = initial.recover().tail

    started = initial.append(
        first_id, StepState.RUNNING, expected_revision=0,
        at_ms=100, retained=genesis,
    )
    interleaved = SyntheticPlanJournal(path, _steps()).append(
        second_id, StepState.RUNNING, expected_revision=0,
        at_ms=110, retained=started.tail,
    )
    assert sorted(interleaved.ambiguous_running_steps) == ["alpha", "beta"]

    # Genesis remains a valid *historical prefix*, but it must never
    # make a stale per-step expected revision valid again.
    with pytest.raises((PlanConflictError, SyntheticPlanJournalRejected)):
        SyntheticPlanJournal(path, _steps()).append(
            first_id, terminal, expected_revision=0,
            at_ms=120, retained=genesis,
        )
    after_denial = SyntheticPlanJournal(path, _steps()).recover(
        retained=genesis,
    )
    assert after_denial.tail == interleaved.tail
    assert after_denial.dispatch_authorized is False
    assert after_denial.automatic_replay_authorized is False

    final = SyntheticPlanJournal(path, _steps()).append(
        first_id, terminal, expected_revision=1,
        at_ms=120, retained=genesis,
    )
    statuses = {
        name: (state, revision)
        for name, state, revision in final.step_statuses
    }
    assert statuses[first_id] == (terminal.value, 2)
    assert statuses[second_id] == ("running", 1)
    assert final.ambiguous_running_steps == (second_id,)
    assert final.dispatch_authorized is False
    assert final.automatic_replay_authorized is False
    assert SyntheticPlanJournal(path, _steps()).recover(
        retained=genesis,
    ).tail == final.tail

    with sqlite3.connect(path) as conn:
        events = conn.execute(
            "SELECT seq,step_id,to_state,resulting_revision "
            "FROM synthetic_plan_events ORDER BY seq"
        ).fetchall()
    assert events == [
        (1, first_id, "running", 1),
        (2, second_id, "running", 1),
        (3, first_id, terminal.value, 2),
    ]
