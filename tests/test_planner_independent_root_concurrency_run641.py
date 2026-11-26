"""Two independent Planner roots may advance concurrently without replaying WRITE.

Synthetic journals persist local state only. All data lives in disposable SQLite,
with no backend calls or automatic restart authorization.
"""

from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
from threading import Barrier

import pytest

from ark.agency.contracts import PlanConflictError, PlanStep, StepState, ToolCall
from ark.agency.planner_journal_review import SyntheticPlanJournal


def _steps():
    return (
        PlanStep("root_a", ToolCall("fixture", "offline", "local", {"n": 1})),
        PlanStep("child_a", ToolCall("fixture", "offline", "local", {"n": 2}), ("root_a",)),
        PlanStep("root_b", ToolCall("fixture", "offline", "local", {"n": 3})),
        PlanStep("child_b", ToolCall("fixture", "offline", "local", {"n": 4}), ("root_b",)),
    )


@pytest.mark.parametrize("terminal", [StepState.FAILED, StepState.CANCELLED])
def test_concurrent_unrelated_root_appends_survive_restart(tmp_path, terminal):
    path = tmp_path / "parallel-planner.sqlite"
    steps = _steps()
    first = SyntheticPlanJournal(path, steps)
    second = SyntheticPlanJournal(path, steps)
    baseline = first.recover().tail
    barrier = Barrier(2)

    def append_root(args):
        journal, name = args
        barrier.wait(timeout=10)
        return journal.append(
            name, StepState.RUNNING, expected_revision=0, at_ms=50,
            retained=baseline,
        )

    with ThreadPoolExecutor(max_workers=2) as executor:
        results = list(executor.map(append_root, (
            (first, "root_a"), (second, "root_b"),
        )))
    assert {r.tail.event_count for r in results} == {1, 2}
    restarted = SyntheticPlanJournal(path, steps)
    running = restarted.recover(retained=baseline)
    assert running.tail.event_count == 2
    assert running.ambiguous_running_steps == ("root_a", "root_b")
    assert running.dispatch_authorized is False
    assert running.automatic_replay_authorized is False

    stopped = restarted.append(
        "root_a", terminal, expected_revision=1, at_ms=51,
        retained=running.tail,
    )
    state = {name: (value, rev) for name, value, rev in stopped.step_statuses}
    assert state["child_a"] == ("blocked", 1)
    assert state["root_b"] == ("running", 1)
    assert state["child_b"] == ("pending", 0)
    with pytest.raises(PlanConflictError):
        restarted.append(
            "child_a", StepState.RUNNING, expected_revision=1, at_ms=52,
        )

    passed = SyntheticPlanJournal(path, steps).append(
        "root_b", StepState.SUCCEEDED, expected_revision=1, at_ms=52,
        retained=stopped.tail,
    )
    child = SyntheticPlanJournal(path, steps).append(
        "child_b", StepState.RUNNING, expected_revision=0, at_ms=53,
        retained=passed.tail,
    )
    latest = SyntheticPlanJournal(path, steps).recover(retained=baseline)
    assert latest == child
    assert latest.tail.event_count == 5
    assert latest.ambiguous_running_steps == ("child_b",)
    assert latest.automatic_replay_authorized is False
