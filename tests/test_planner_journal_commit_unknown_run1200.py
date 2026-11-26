"""Run1200: Planner journal COMMIT ambiguity and hard-process-exit recovery."""

from __future__ import annotations

import multiprocessing
import os
import sqlite3
from pathlib import Path

import pytest

from ark.agency.contracts import PlanStep, StepState, ToolCall
from ark.agency.planner import PlanGraph
from ark.agency.planner_journal import (
    PlannerJournal,
    PlannerJournalCommitUnknown,
)


def _steps() -> tuple[PlanStep, ...]:
    return (
        PlanStep(
            "root",
            ToolCall(
                "fixture.root",
                "fixture.read",
                "synthetic:private",
                {"private_fixture": "raw-sensitive-fixture"},
            ),
        ),
        PlanStep(
            "child",
            ToolCall(
                "fixture.child",
                "fixture.read",
                "synthetic:private",
                {"value": "child"},
            ),
            ("root",),
        ),
    )


class _CommitBoundary:
    def __init__(self, connection: sqlite3.Connection, *, durable: bool) -> None:
        self.connection = connection
        self.durable = durable
        self.commit_attempts = 0

    def execute(self, statement: str, *args):
        if statement == "COMMIT":
            self.commit_attempts += 1
            if self.durable:
                self.connection.execute(statement, *args)
            else:
                self.connection.execute("ROLLBACK")
            raise sqlite3.OperationalError(
                "synthetic Planner COMMIT acknowledgement lost"
            )
        return self.connection.execute(statement, *args)

    def __getattr__(self, name):
        return getattr(self.connection, name)


@pytest.mark.parametrize("durable", (False, True), ids=("rolled-back", "committed"))
def test_transition_commit_ack_loss_requires_cold_recovery_not_retry(
    tmp_path: Path,
    durable: bool,
) -> None:
    path = tmp_path / "planner-commit-unknown.sqlite3"
    journal = PlannerJournal(path)
    steps = _steps()
    graph = PlanGraph(steps)
    journal.create_plan("commit-unknown-plan", graph)

    native_connect = journal._connect
    boundaries: list[_CommitBoundary] = []

    def connect_with_lost_commit_ack():
        boundary = _CommitBoundary(native_connect(), durable=durable)
        boundaries.append(boundary)
        return boundary

    journal._connect = connect_with_lost_commit_ack
    with pytest.raises(
        PlannerJournalCommitUnknown,
        match="recover before any retry",
    ):
        journal.transition(
            "commit-unknown-plan",
            graph,
            "root",
            StepState.RUNNING,
            expected_revision=0,
            expected_sequence=0,
        )

    assert len(boundaries) == 1
    assert boundaries[0].commit_attempts == 1

    # Resolve only by a fresh instance's durable readback. Do not retry the
    # transition or infer the outcome from the raised COMMIT exception.
    cold = PlannerJournal(path)
    recovered = cold.recover("commit-unknown-plan", steps)
    with sqlite3.connect(path) as connection:
        count = connection.execute(
            "SELECT COUNT(*) FROM planner_journal_events"
        ).fetchone()[0]
        assert connection.execute("PRAGMA quick_check").fetchone() == ("ok",)

    if durable:
        assert count == 1
        assert recovered.sequence == 1
        assert recovered.graph.statuses()["root"].state is StepState.RUNNING
        assert recovered.ambiguous_running_step_ids == ("root",)
    else:
        assert count == 0
        assert recovered.sequence == 0
        assert recovered.graph.statuses()["root"].state is StepState.PENDING
        assert recovered.ambiguous_running_step_ids == ()

    assert recovered.dispatch_authorized is False
    assert recovered.automatic_replay_authorized is False
    assert b"raw-sensitive-fixture" not in path.read_bytes()
    assert boundaries[0].commit_attempts == 1


def _hard_exit_after_native_commit(database: str) -> None:
    path = Path(database)
    steps = _steps()
    journal = PlannerJournal(path)
    graph = journal.recover("hard-exit-plan", steps).graph
    native_connect = journal._connect

    class ExitAfterCommit:
        def __init__(self, connection: sqlite3.Connection) -> None:
            self.connection = connection

        def execute(self, statement: str, *args):
            result = self.connection.execute(statement, *args)
            if statement == "COMMIT":
                # Deliberately bypass Python cleanup after native COMMIT.
                os._exit(73)
            return result

        def __getattr__(self, name):
            return getattr(self.connection, name)

    journal._connect = lambda: ExitAfterCommit(native_connect())
    journal.transition(
        "hard-exit-plan",
        graph,
        "root",
        StepState.RUNNING,
        expected_revision=0,
        expected_sequence=0,
    )
    os._exit(74)


def test_hard_process_exit_after_commit_recovers_running_as_ambiguous(
    tmp_path: Path,
) -> None:
    path = tmp_path / "planner-hard-exit.sqlite3"
    journal = PlannerJournal(path)
    steps = _steps()
    journal.create_plan("hard-exit-plan", PlanGraph(steps))

    process = multiprocessing.get_context("spawn").Process(
        target=_hard_exit_after_native_commit,
        args=(str(path),),
    )
    process.start()
    process.join(timeout=30)
    if process.is_alive():
        process.terminate()
        process.join(timeout=5)
        pytest.fail("Planner hard-exit fixture did not terminate")
    assert process.exitcode == 73

    cold = PlannerJournal(path)
    recovered = cold.recover("hard-exit-plan", steps)
    assert recovered.sequence == 1
    assert recovered.graph.statuses()["root"].state is StepState.RUNNING
    assert recovered.ambiguous_running_step_ids == ("root",)
    assert recovered.graph.ready_steps() == ()
    assert recovered.dispatch_authorized is False
    assert recovered.automatic_replay_authorized is False
    with sqlite3.connect(path) as connection:
        assert connection.execute("PRAGMA quick_check").fetchone() == ("ok",)
        assert connection.execute(
            "SELECT COUNT(*) FROM planner_journal_events"
        ).fetchone() == (1,)
    assert b"raw-sensitive-fixture" not in path.read_bytes()
