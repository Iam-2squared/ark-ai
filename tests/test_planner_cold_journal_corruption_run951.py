"""Run951: synthetic Planner journal recovery refuses corrupt historical rows.

The Planner and SQLite journal are synthetic. RUNNING/UNKNOWN and valid
historical digests remain manual-review states without dispatch/replay grants.
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
    return (
        PlanStep(
            "step",
            ToolCall("synthetic.read", "synthetic.read", "local-only"),
        ),
    )


@pytest.mark.parametrize("tamper", (
    "wrong-schema-version",
    "extra-event-column",
    "missing-first-event",
    "header-event-count-rewind",
    "changed-transition-clock",
    "changed-transition-state",
))
def test_cold_planner_denies_invalid_replayed_history_without_repair(
    tmp_path, tamper: str,
) -> None:
    path = tmp_path / "synthetic-corrupt-plan.sqlite3"
    journal = SyntheticPlanJournal(path, _steps())
    genesis = journal.recover().tail
    running = journal.append(
        "step", StepState.RUNNING, expected_revision=0,
        at_ms=100, retained=genesis,
    )
    completed = journal.append(
        "step", StepState.SUCCEEDED, expected_revision=1,
        at_ms=200, retained=running.tail,
    )
    assert completed.dispatch_authorized is False
    assert completed.automatic_replay_authorized is False
    assert completed.ambiguous_running_steps == ()

    with sqlite3.connect(path) as conn:
        if tamper == "wrong-schema-version":
            conn.execute("PRAGMA user_version=2")
        elif tamper == "extra-event-column":
            conn.execute(
                "ALTER TABLE synthetic_plan_events ADD COLUMN injected TEXT"
            )
        elif tamper == "missing-first-event":
            conn.execute("DELETE FROM synthetic_plan_events WHERE seq=1")
        elif tamper == "header-event-count-rewind":
            conn.execute(
                "UPDATE synthetic_plan_header SET event_count=1 WHERE id=1"
            )
        elif tamper == "changed-transition-clock":
            conn.execute(
                "UPDATE synthetic_plan_events SET occurred_at_ms=201 WHERE seq=2"
            )
        else:
            conn.execute(
                "UPDATE synthetic_plan_events SET to_state='failed' WHERE seq=2"
            )

    def image() -> tuple[object, object, object]:
        with sqlite3.connect(path) as conn:
            return (
                conn.execute("PRAGMA user_version").fetchone(),
                conn.execute("SELECT * FROM synthetic_plan_header").fetchall(),
                conn.execute(
                    "SELECT * FROM synthetic_plan_events ORDER BY seq"
                ).fetchall(),
            )

    corrupted = image()
    with pytest.raises((SyntheticPlanJournalRejected, PlanConflictError)):
        SyntheticPlanJournal(path, _steps()).recover(retained=genesis)
    assert image() == corrupted


def test_intact_cold_planner_history_remains_nonexecuting(tmp_path) -> None:
    path = tmp_path / "synthetic-intact-plan.sqlite3"
    journal = SyntheticPlanJournal(path, _steps())
    genesis = journal.recover().tail
    running = journal.append(
        "step", StepState.RUNNING, expected_revision=0,
        at_ms=100, retained=genesis,
    )
    cold = SyntheticPlanJournal(path, _steps()).recover(retained=genesis)
    assert cold.tail == running.tail
    assert cold.ambiguous_running_steps == ("step",)
    assert cold.dispatch_authorized is False
    assert cold.automatic_replay_authorized is False
