"""Cold-restart Planner DAG quarantine and durable event prefix regression.

Only a temporary SQLite journal and synthetic ToolCall identities are used.
A RUNNING record denotes an unknown outcome, never permission to retry.
"""

from __future__ import annotations

import sqlite3
from contextlib import closing

import pytest

from ark.agency.contracts import PlanConflictError, PlanStep, StepState, ToolCall
from ark.agency.planner_journal_review import SyntheticPlanJournal


def _steps() -> tuple[PlanStep, ...]:
    return (
        PlanStep("root", ToolCall("fixture", "local.read", "test", {"i": 1})),
        PlanStep(
            "child",
            ToolCall("fixture", "local.read", "test", {"i": 2}),
            depends_on=("root",),
        ),
        PlanStep(
            "grandchild",
            ToolCall("fixture", "local.write", "test", {"i": 3}),
            depends_on=("child",),
        ),
        PlanStep(
            "independent", ToolCall("fixture", "local.read", "test", {"i": 4})
        ),
    )


def _count(path) -> int:
    with closing(sqlite3.connect(path)) as conn:
        return conn.execute(
            "SELECT COUNT(*) FROM synthetic_plan_events"
        ).fetchone()[0]


def test_recovered_unknown_root_is_never_a_runnable_receipt(tmp_path) -> None:
    path = tmp_path / "planner.sqlite3"
    first = SyntheticPlanJournal(path, _steps())
    written = first.append("root", StepState.RUNNING, expected_revision=0, at_ms=10)
    retained = written.tail

    for _ in range(3):
        restarted = SyntheticPlanJournal(path, _steps())
        snapshot = restarted.recover(retained=retained)
        assert snapshot.tail == retained
        assert snapshot.ambiguous_running_steps == ("root",)
        assert snapshot.dispatch_authorized is False
        assert snapshot.automatic_replay_authorized is False
        assert ("child", "pending", 0) in snapshot.step_statuses
        assert ("grandchild", "pending", 0) in snapshot.step_statuses
    assert _count(path) == 1


def test_cold_failure_cascades_transitively_without_touching_other_root(tmp_path) -> None:
    path = tmp_path / "planner.sqlite3"
    first = SyntheticPlanJournal(path, _steps())
    running = first.append("root", StepState.RUNNING, expected_revision=0, at_ms=10)
    restarted = SyntheticPlanJournal(path, _steps())
    failed = restarted.append(
        "root", StepState.FAILED, expected_revision=1, at_ms=11,
        retained=running.tail,
    )
    recovered = SyntheticPlanJournal(path, _steps()).recover(retained=running.tail)
    assert recovered.tail == failed.tail
    assert recovered.ambiguous_running_steps == ()
    assert ("root", "failed", 2) in recovered.step_statuses
    assert ("child", "blocked", 1) in recovered.step_statuses
    assert ("grandchild", "blocked", 1) in recovered.step_statuses
    assert ("independent", "pending", 0) in recovered.step_statuses
    assert recovered.dispatch_authorized is False
    assert recovered.automatic_replay_authorized is False
    assert _count(path) == 2


def test_unknown_parent_forbids_dependency_dispatch_and_journal_append(tmp_path) -> None:
    path = tmp_path / "planner.sqlite3"
    first = SyntheticPlanJournal(path, _steps())
    running = first.append("root", StepState.RUNNING, expected_revision=0, at_ms=10)
    restarted = SyntheticPlanJournal(path, _steps())
    with pytest.raises(PlanConflictError, match="dependencies"):
        restarted.append(
            "child", StepState.RUNNING, expected_revision=0, at_ms=11,
            retained=running.tail,
        )
    intact = SyntheticPlanJournal(path, _steps()).recover(retained=running.tail)
    assert intact.tail == running.tail
    assert intact.ambiguous_running_steps == ("root",)
    assert _count(path) == 1
