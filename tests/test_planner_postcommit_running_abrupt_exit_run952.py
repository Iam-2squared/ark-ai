"""Run952: Planner crash after durable RUNNING must be cold UNKNOWN/deny-only.

Only synthetic plan state and local SQLite are involved. There is no tool
execution, no retry authority and no claim of authenticated external outcome.
"""

from __future__ import annotations

import sqlite3
import subprocess
import sys

import pytest

from ark.agency import PlanConflictError, PlanStep, StepState, ToolCall
from ark.agency.planner_journal_review import (
    SyntheticPlanJournal,
    SyntheticPlanJournalRejected,
)


def _steps() -> tuple[PlanStep, ...]:
    call = ToolCall("synthetic.read", "synthetic.read", "local-only")
    return (PlanStep("alpha", call), PlanStep("beta", call))


@pytest.mark.parametrize("running_step", ("alpha", "beta"))
def test_cold_planner_never_retries_crashed_running_step(
    tmp_path, running_step: str,
) -> None:
    path = tmp_path / "synthetic-plan-child-exit.sqlite3"
    genesis = SyntheticPlanJournal(path, _steps()).recover().tail
    code = """
import os
import sys
from pathlib import Path
from ark.agency import PlanStep, StepState, ToolCall
from ark.agency.planner_journal_review import SyntheticPlanJournal
call = ToolCall("synthetic.read", "synthetic.read", "local-only")
steps = (PlanStep("alpha", call), PlanStep("beta", call))
journal = SyntheticPlanJournal(Path(sys.argv[1]), steps)
witness = journal.recover().tail
journal.append(
    sys.argv[2], StepState.RUNNING, expected_revision=0,
    at_ms=100, retained=witness,
)
os._exit(31)
"""
    completed = subprocess.run(
        [sys.executable, "-c", code, str(path), running_step],
        capture_output=True, text=True, timeout=30, check=False,
    )
    assert completed.returncode == 31, completed.stderr

    cold = SyntheticPlanJournal(path, _steps())
    recovery = cold.recover(retained=genesis)
    other = "beta" if running_step == "alpha" else "alpha"
    assert dict(
        (step, (state, revision))
        for step, state, revision in recovery.step_statuses
    ) == {
        running_step: ("running", 1),
        other: ("pending", 0),
    }
    assert recovery.ambiguous_running_steps == (running_step,)
    assert recovery.dispatch_authorized is False
    assert recovery.automatic_replay_authorized is False

    with sqlite3.connect(path) as conn:
        event_rows = conn.execute(
            "SELECT seq,step_id,to_state,expected_revision "
            "FROM synthetic_plan_events ORDER BY seq"
        ).fetchall()
    assert event_rows == [(1, running_step, "running", 0)]
    with pytest.raises((PlanConflictError, SyntheticPlanJournalRejected)):
        cold.append(
            running_step, StepState.RUNNING, expected_revision=0,
            at_ms=101, retained=genesis,
        )
    with sqlite3.connect(path) as conn:
        assert conn.execute(
            "SELECT seq,step_id,to_state,expected_revision "
            "FROM synthetic_plan_events ORDER BY seq"
        ).fetchall() == event_rows
    assert SyntheticPlanJournal(path, _steps()).recover(
        retained=genesis,
    ).ambiguous_running_steps == (running_step,)
