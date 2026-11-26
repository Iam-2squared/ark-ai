"""Competing offline terminal outcomes must commit only one Planner branch.

Disposable SQLite journal only: no backend, trusted clock, human approval,
or automatic recovery/replay authority is asserted.
"""

from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
from threading import Barrier

import pytest

from ark.agency.contracts import PlanConflictError, PlanStep, StepState, ToolCall
from ark.agency.planner_journal_review import SyntheticPlanJournal


def _steps():
    return (
        PlanStep("root", ToolCall("fixture", "offline", "local", {"id": 1})),
        PlanStep(
            "child", ToolCall("fixture", "offline", "local", {"id": 2}),
            ("root",),
        ),
        PlanStep("independent", ToolCall("fixture", "offline", "local", {"id": 3})),
    )


@pytest.mark.parametrize("denial", (StepState.FAILED, StepState.CANCELLED))
def test_competing_terminal_outcomes_cannot_split_persisted_cascade(
    tmp_path, denial,
):
    path = tmp_path / "terminal-race.sqlite"
    steps = _steps()
    first = SyntheticPlanJournal(path, steps)
    second = SyntheticPlanJournal(path, steps)
    genesis = first.recover().tail
    running = first.append(
        "root", StepState.RUNNING, expected_revision=0,
        at_ms=100, retained=genesis,
    )
    assert running.ambiguous_running_steps == ("root",)
    gate = Barrier(2)

    def attempt(args):
        journal, terminal = args
        gate.wait(timeout=10)
        try:
            result = journal.append(
                "root", terminal, expected_revision=1,
                at_ms=101, retained=running.tail,
            )
        except PlanConflictError:
            return ("stale", terminal, None)
        return ("committed", terminal, result)

    with ThreadPoolExecutor(max_workers=2) as workers:
        attempts = list(workers.map(
            attempt, ((first, denial), (second, StepState.SUCCEEDED)),
        ))
    assert sorted(item[0] for item in attempts) == ["committed", "stale"]
    winner = next(item for item in attempts if item[0] == "committed")
    restarted = SyntheticPlanJournal(path, steps)
    recovered = restarted.recover(retained=genesis)
    assert recovered == winner[2]
    assert recovered.tail.event_count == 2
    assert recovered.ambiguous_running_steps == ()
    assert recovered.dispatch_authorized is False
    assert recovered.automatic_replay_authorized is False

    states = {name: (status, rev) for name, status, rev in recovered.step_statuses}
    assert states["root"] == (winner[1].value, 2)
    assert states["independent"] == ("pending", 0)
    assert states["child"] == (
        ("pending", 0)
        if winner[1] is StepState.SUCCEEDED
        else ("blocked", 1)
    )

    with pytest.raises(PlanConflictError):
        restarted.append(
            "root", denial if winner[1] is StepState.SUCCEEDED
            else StepState.SUCCEEDED,
            expected_revision=1, at_ms=102, retained=running.tail,
        )
    assert SyntheticPlanJournal(path, steps).recover(retained=genesis) == recovered
