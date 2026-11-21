"""Run949: durable Planner terminal cascades remain quarantined after restart.

This exercises a synthetic DAG and SQLite journal only. No registered tool,
external executor, automatic retry, approval or real dispatch is involved.
"""

from __future__ import annotations

import json
import subprocess
import sys
from dataclasses import asdict

import pytest

from ark.agency import PlanConflictError, PlanStep, StepState, ToolCall
from ark.agency.planner_journal_review import (
    SyntheticPlanJournal,
    SyntheticPlanJournalRejected,
)

_COLD = """
import json
import sys
from pathlib import Path
from ark.agency import PlanStep, ToolCall
from ark.agency.planner_journal_review import SyntheticPlanJournal, SyntheticPlanTail
call = ToolCall("synthetic.read", "synthetic.read", "local-only")
steps = (
    PlanStep("left", call),
    PlanStep("left-child", call, ("left",)),
    PlanStep("right", call),
    PlanStep("right-child", call, ("right",)),
    PlanStep("join", call, ("left-child", "right-child")),
)
retained = SyntheticPlanTail(**json.loads(sys.argv[2]))
state = SyntheticPlanJournal(Path(sys.argv[1]), steps).recover(retained=retained)
print(json.dumps({
    "statuses": state.step_statuses,
    "running": state.ambiguous_running_steps,
    "dispatch": state.dispatch_authorized,
    "replay": state.automatic_replay_authorized,
}, sort_keys=True))
"""


def _steps() -> tuple[PlanStep, ...]:
    call = ToolCall("synthetic.read", "synthetic.read", "local-only")
    return (
        PlanStep("left", call),
        PlanStep("left-child", call, ("left",)),
        PlanStep("right", call),
        PlanStep("right-child", call, ("right",)),
        PlanStep("join", call, ("left-child", "right-child")),
    )


@pytest.mark.parametrize(("left_terminal", "right_terminal"), (
    (StepState.FAILED, StepState.FAILED),
    (StepState.FAILED, StepState.CANCELLED),
    (StepState.CANCELLED, StepState.FAILED),
    (StepState.CANCELLED, StepState.CANCELLED),
))
def test_two_cold_terminal_waves_never_reopen_blocked_dependencies(
    tmp_path, left_terminal: StepState, right_terminal: StepState,
) -> None:
    path = tmp_path / "synthetic-plan-journal.sqlite3"
    initial = SyntheticPlanJournal(path, _steps())
    genesis = initial.recover().tail
    first = initial.append(
        "left", StepState.RUNNING, expected_revision=0,
        at_ms=100, retained=genesis,
    )
    terminal = SyntheticPlanJournal(path, _steps()).append(
        "left", left_terminal, expected_revision=1,
        at_ms=110, retained=first.tail,
    )
    first_wave = dict(
        (name, (state, revision))
        for name, state, revision in terminal.step_statuses
    )
    assert first_wave["left-child"] == ("blocked", 1)
    assert first_wave["join"] == ("blocked", 1)
    assert first_wave["right"] == ("pending", 0)

    second = SyntheticPlanJournal(path, _steps()).append(
        "right", StepState.RUNNING, expected_revision=0,
        at_ms=120, retained=terminal.tail,
    )
    assert second.ambiguous_running_steps == ("right",)
    final = SyntheticPlanJournal(path, _steps()).append(
        "right", right_terminal, expected_revision=1,
        at_ms=130, retained=second.tail,
    )
    expected_statuses = {
        "left": (left_terminal.value, 2),
        "left-child": ("blocked", 1),
        "right": (right_terminal.value, 2),
        "right-child": ("blocked", 1),
        "join": ("blocked", 1),
    }
    assert {
        name: (state, revision)
        for name, state, revision in final.step_statuses
    } == expected_statuses
    assert final.ambiguous_running_steps == ()
    assert final.dispatch_authorized is False
    assert final.automatic_replay_authorized is False

    cold = subprocess.run(
        [sys.executable, "-c", _COLD, str(path),
         json.dumps(asdict(genesis), sort_keys=True)],
        capture_output=True, text=True, check=True, timeout=20,
    )
    observed = json.loads(cold.stdout)
    assert {
        name: (state, revision)
        for name, state, revision in observed["statuses"]
    } == expected_statuses
    assert observed["running"] == []
    assert observed["dispatch"] is False
    assert observed["replay"] is False

    with pytest.raises((PlanConflictError, SyntheticPlanJournalRejected)):
        SyntheticPlanJournal(path, _steps()).append(
            "join", StepState.RUNNING, expected_revision=1,
            at_ms=140, retained=final.tail,
        )
    assert SyntheticPlanJournal(path, _steps()).recover(
        retained=genesis,
    ).tail == final.tail
