"""Run1440: PlannerJournal recovery preserves a running sibling and terminal fan-in."""

from __future__ import annotations

from pathlib import Path

import pytest

from ark.agency.contracts import (
    PlanStep,
    StepState,
    ToolCall,
)
from ark.agency.planner import PlanGraph
from ark.agency.planner_journal import (
    PlannerJournal,
    PlannerJournalConflictError,
)


def _steps() -> tuple[PlanStep, ...]:
    call = ToolCall(
        "fixture.inspect",
        "fixture.read",
        "synthetic:private",
        {"fixture": "run1440"},
    )
    return (
        PlanStep("root", call),
        PlanStep("left", call, ("root",)),
        PlanStep("right", call, ("root",)),
        PlanStep("join", call, ("left", "right")),
        PlanStep("leaf", call, ("join",)),
        PlanStep("independent", call),
    )


def _state(graph: PlanGraph, step_id: str) -> tuple[StepState, int]:
    status = graph.statuses()[step_id]
    return status.state, status.revision


def test_cold_recovery_keeps_running_sibling_and_terminal_fanin_blocked(
    tmp_path: Path,
) -> None:
    path = tmp_path / "planner-diamond-running-barrier.sqlite3"
    plan_id = "run1440-diamond-running-barrier"
    steps = _steps()
    journal = PlannerJournal(path)
    graph = PlanGraph(steps)
    journal.create_plan(plan_id, graph)

    root_running = journal.transition(
        plan_id, graph, "root", StepState.RUNNING,
        expected_revision=0, expected_sequence=0,
    )
    root_succeeded = journal.transition(
        plan_id, root_running.graph, "root", StepState.SUCCEEDED,
        expected_revision=1, expected_sequence=1,
    )
    left_running = journal.transition(
        plan_id, root_succeeded.graph, "left", StepState.RUNNING,
        expected_revision=0, expected_sequence=2,
    )
    right_running = journal.transition(
        plan_id, left_running.graph, "right", StepState.RUNNING,
        expected_revision=0, expected_sequence=3,
    )
    left_failed = journal.transition(
        plan_id, right_running.graph, "left", StepState.FAILED,
        expected_revision=1, expected_sequence=4,
    )

    assert _state(left_failed.graph, "left") == (StepState.FAILED, 2)
    assert _state(left_failed.graph, "right") == (StepState.RUNNING, 1)
    assert _state(left_failed.graph, "join") == (StepState.BLOCKED, 1)
    assert _state(left_failed.graph, "leaf") == (StepState.BLOCKED, 1)
    assert _state(left_failed.graph, "independent") == (StepState.PENDING, 0)

    cold = PlannerJournal(path).recover(plan_id, steps)
    assert cold.sequence == 5
    assert cold.ambiguous_running_step_ids == ("right",)
    assert _state(cold.graph, "right") == (StepState.RUNNING, 1)
    assert _state(cold.graph, "join") == (StepState.BLOCKED, 1)
    assert _state(cold.graph, "leaf") == (StepState.BLOCKED, 1)
    assert cold.dispatch_authorized is False
    assert cold.automatic_replay_authorized is False

    with pytest.raises(PlannerJournalConflictError):
        journal.transition(
            plan_id, cold.graph, "join", StepState.RUNNING,
            expected_revision=1, expected_sequence=5,
        )

    # Resolving the independent RUNNING branch cannot resurrect a join that
    # was already terminally blocked by its other dependency.
    right_succeeded = journal.transition(
        plan_id, cold.graph, "right", StepState.SUCCEEDED,
        expected_revision=1, expected_sequence=5,
    )
    final = PlannerJournal(path).recover(plan_id, steps)
    assert right_succeeded.receipt.sequence == 6
    assert final.sequence == 6
    assert final.ambiguous_running_step_ids == ()
    assert _state(final.graph, "right") == (StepState.SUCCEEDED, 2)
    assert _state(final.graph, "join") == (StepState.BLOCKED, 1)
    assert _state(final.graph, "leaf") == (StepState.BLOCKED, 1)
    assert _state(final.graph, "independent") == (StepState.PENDING, 0)
    assert final.dispatch_authorized is False
    assert final.automatic_replay_authorized is False
