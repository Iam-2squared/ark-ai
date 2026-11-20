"""Run1018: lost Planner COMMIT acknowledgements remain UNKNOWN after restart.

Only synthetic PlanStep/ToolCall descriptions and disposable local SQLite are
used. No ToolBackend is dispatched and no automatic replay is authorized.
"""

from __future__ import annotations

import sqlite3
from pathlib import Path

import pytest

from ark.agency.contracts import PlanConflictError, PlanStep, StepState, ToolCall
from ark.agency.planner_journal_review import SyntheticPlanJournal


def _steps() -> tuple[PlanStep, ...]:
    call = ToolCall("fixture", "offline", "local", {"n": 1})
    return (
        PlanStep("root", call),
        PlanStep("child", call, ("root",)),
        PlanStep("independent", call),
    )


def _lose_next_commit_acknowledgement(journal, monkeypatch) -> list[bool]:
    native_connect = journal._connect
    committed: list[bool] = []

    class CommitAcknowledgementLost:
        def __init__(self, connection: sqlite3.Connection) -> None:
            self.connection = connection

        def execute(self, *args, **kwargs):
            return self.connection.execute(*args, **kwargs)

        def commit(self) -> None:
            self.connection.commit()
            committed.append(True)
            raise sqlite3.OperationalError(
                "synthetic Planner COMMIT acknowledgement lost",
            )

        def rollback(self) -> None:
            self.connection.rollback()

        def close(self) -> None:
            self.connection.close()

        def __getattr__(self, name: str):
            return getattr(self.connection, name)

    def connect(*args, **kwargs):
        return CommitAcknowledgementLost(native_connect(*args, **kwargs))

    monkeypatch.setattr(journal, "_connect", connect)
    return committed


def test_lost_running_commit_acknowledgement_recovers_as_ambiguous_no_replay(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    path = tmp_path / "planner-running-commit-unknown.sqlite3"
    steps = _steps()
    journal = SyntheticPlanJournal(path, steps)
    genesis = journal.recover()
    committed = _lose_next_commit_acknowledgement(journal, monkeypatch)

    with pytest.raises(
        sqlite3.OperationalError,
        match="Planner COMMIT acknowledgement lost",
    ):
        journal.append(
            "root",
            StepState.RUNNING,
            expected_revision=0,
            at_ms=10,
            retained=genesis.tail,
        )

    assert committed == [True]
    cold = SyntheticPlanJournal(path, steps)
    recovered = cold.recover(retained=genesis.tail)
    statuses = {
        step: (state, revision)
        for step, state, revision in recovered.step_statuses
    }
    assert recovered.tail.event_count == 1
    assert statuses == {
        "root": ("running", 1),
        "child": ("pending", 0),
        "independent": ("pending", 0),
    }
    assert recovered.ambiguous_running_steps == ("root",)
    assert recovered.dispatch_authorized is False
    assert recovered.automatic_replay_authorized is False

    with sqlite3.connect(path) as connection:
        events = connection.execute(
            "SELECT seq,step_id,to_state,expected_revision "
            "FROM synthetic_plan_events ORDER BY seq"
        ).fetchall()
        assert connection.execute("PRAGMA quick_check").fetchone() == ("ok",)
    assert events == [(1, "root", "running", 0)]

    with pytest.raises(PlanConflictError, match="revision"):
        cold.append(
            "root",
            StepState.RUNNING,
            expected_revision=0,
            at_ms=11,
            retained=genesis.tail,
        )
    assert SyntheticPlanJournal(path, steps).recover(
        retained=genesis.tail,
    ).tail == recovered.tail


def test_lost_terminal_commit_acknowledgement_recovers_cascade_without_replay(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    path = tmp_path / "planner-terminal-commit-unknown.sqlite3"
    steps = _steps()
    journal = SyntheticPlanJournal(path, steps)
    running = journal.append(
        "root",
        StepState.RUNNING,
        expected_revision=0,
        at_ms=10,
    )
    committed = _lose_next_commit_acknowledgement(journal, monkeypatch)

    with pytest.raises(
        sqlite3.OperationalError,
        match="Planner COMMIT acknowledgement lost",
    ):
        journal.append(
            "root",
            StepState.FAILED,
            expected_revision=1,
            at_ms=11,
            retained=running.tail,
        )

    assert committed == [True]
    cold = SyntheticPlanJournal(path, steps)
    recovered = cold.recover(retained=running.tail)
    statuses = {
        step: (state, revision)
        for step, state, revision in recovered.step_statuses
    }
    assert recovered.tail.event_count == 2
    assert statuses == {
        "root": ("failed", 2),
        "child": ("blocked", 1),
        "independent": ("pending", 0),
    }
    assert recovered.ambiguous_running_steps == ()
    assert recovered.dispatch_authorized is False
    assert recovered.automatic_replay_authorized is False

    with sqlite3.connect(path) as connection:
        events = connection.execute(
            "SELECT seq,step_id,to_state,expected_revision "
            "FROM synthetic_plan_events ORDER BY seq"
        ).fetchall()
        assert connection.execute("PRAGMA quick_check").fetchone() == ("ok",)
    assert events == [
        (1, "root", "running", 0),
        (2, "root", "failed", 1),
    ]

    with pytest.raises(PlanConflictError, match="revision"):
        cold.append(
            "root",
            StepState.FAILED,
            expected_revision=1,
            at_ms=12,
            retained=running.tail,
        )
    assert SyntheticPlanJournal(path, steps).recover(
        retained=running.tail,
    ).tail == recovered.tail
