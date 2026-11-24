"""Run1241: production Planner terminal COMMIT survives a hard process exit."""

from __future__ import annotations

import multiprocessing
import os
import sqlite3
from pathlib import Path

import pytest

from ark.agency.contracts import PlanStep, StepState, ToolCall
from ark.agency.planner import PlanGraph
from ark.agency.planner_journal import PlannerJournal


def _steps() -> tuple[PlanStep, ...]:
    call = ToolCall(
        "fixture.root",
        "fixture.read",
        "synthetic:private",
        {"private_fixture": "raw-sensitive-terminal-fixture"},
    )
    return (
        PlanStep("root", call),
        PlanStep("dependent", call, ("root",)),
        PlanStep("independent", call),
    )


def _hard_exit_after_terminal_commit(database: str) -> None:
    path = Path(database)
    steps = _steps()
    journal = PlannerJournal(path)
    graph = journal.recover("terminal-hard-exit-plan", steps).graph
    native_connect = journal._connect

    class ExitAfterCommit:
        def __init__(self, connection: sqlite3.Connection) -> None:
            self.connection = connection

        def execute(self, statement: str, *args):
            result = self.connection.execute(statement, *args)
            if statement == "COMMIT":
                # Bypass Python cleanup immediately after SQLite confirms commit.
                os._exit(74)
            return result

        def __getattr__(self, name):
            return getattr(self.connection, name)

    journal._connect = lambda: ExitAfterCommit(native_connect())
    journal.transition(
        "terminal-hard-exit-plan",
        graph,
        "root",
        StepState.FAILED,
        expected_revision=1,
        expected_sequence=1,
    )
    os._exit(75)


def test_terminal_failure_and_descendant_blocking_survive_native_commit_hard_exit(
    tmp_path: Path,
) -> None:
    path = tmp_path / "planner-terminal-hard-exit.sqlite3"
    steps = _steps()
    journal = PlannerJournal(path)
    initial = PlanGraph(steps)
    journal.create_plan("terminal-hard-exit-plan", initial)
    running = journal.transition(
        "terminal-hard-exit-plan",
        initial,
        "root",
        StepState.RUNNING,
        expected_revision=0,
        expected_sequence=0,
    )
    assert running.receipt.sequence == 1

    process = multiprocessing.get_context("spawn").Process(
        target=_hard_exit_after_terminal_commit,
        args=(str(path),),
    )
    process.start()
    process.join(timeout=30)
    if process.is_alive():
        process.terminate()
        process.join(timeout=5)
        pytest.fail("Planner terminal hard-exit fixture did not terminate")
    assert process.exitcode == 74

    cold = PlannerJournal(path)
    recovered = cold.recover("terminal-hard-exit-plan", steps)
    statuses = recovered.graph.statuses()
    assert statuses["root"].state is StepState.FAILED
    assert statuses["root"].revision == 2
    assert statuses["dependent"].state is StepState.BLOCKED
    assert statuses["dependent"].revision == 1
    assert statuses["independent"].state is StepState.PENDING
    assert statuses["independent"].revision == 0
    assert recovered.sequence == 2
    assert recovered.ambiguous_running_step_ids == ()
    assert recovered.dispatch_authorized is False
    assert recovered.automatic_replay_authorized is False

    with sqlite3.connect(path) as connection:
        assert connection.execute("PRAGMA quick_check").fetchone() == ("ok",)
        assert connection.execute(
            "SELECT sequence,step_id,from_state,to_state,expected_revision "
            "FROM planner_journal_events ORDER BY sequence"
        ).fetchall() == [
            (1, "root", "pending", "running", 0),
            (2, "root", "running", "failed", 1),
        ]

    assert b"raw-sensitive-terminal-fixture" not in path.read_bytes()
