"""Run1268: Planner genesis survives native SQLite COMMIT followed by hard exit."""

from __future__ import annotations

import multiprocessing
import os
import sqlite3
from pathlib import Path

import pytest

from ark.agency.contracts import PlanStep, StepState, ToolCall
from ark.agency.planner import PlanGraph
from ark.agency.planner_journal import PlannerJournal

_PLAN_ID = "genesis-hard-exit-plan"


def _steps() -> tuple[PlanStep, ...]:
    call = ToolCall(
        "fixture.root",
        "fixture.read",
        "synthetic:private",
        {"private_fixture": "raw-sensitive-genesis-hard-exit-fixture"},
    )
    return (PlanStep("root", call),)


def _hard_exit_after_genesis_commit(database: str) -> None:
    path = Path(database)
    journal = PlannerJournal(path)
    native_connect = journal._connect

    class ExitAfterCommit:
        def __init__(self, connection: sqlite3.Connection) -> None:
            self.connection = connection

        def execute(self, statement: str, *args):
            result = self.connection.execute(statement, *args)
            if statement == "COMMIT":
                # SQLite has committed the genesis row; skip cleanup and return.
                os._exit(74)
            return result

        def __getattr__(self, name):
            return getattr(self.connection, name)

    journal._connect = lambda: ExitAfterCommit(native_connect())
    journal.create_plan(_PLAN_ID, PlanGraph(_steps()))
    os._exit(75)


def test_genesis_row_survives_native_commit_hard_exit(tmp_path: Path) -> None:
    path = tmp_path / "planner-genesis-hard-exit.sqlite3"
    PlannerJournal(path)

    process = multiprocessing.get_context("spawn").Process(
        target=_hard_exit_after_genesis_commit,
        args=(str(path),),
    )
    process.start()
    process.join(timeout=30)
    if process.is_alive():
        process.terminate()
        process.join(timeout=5)
        pytest.fail("Planner genesis hard-exit fixture did not terminate")
    assert process.exitcode == 74

    cold = PlannerJournal(path)
    recovered = cold.recover(_PLAN_ID, _steps())
    status = recovered.graph.statuses()["root"]
    assert status.state is StepState.PENDING
    assert status.revision == 0
    assert recovered.sequence == 0
    assert recovered.ambiguous_running_step_ids == ()
    assert recovered.dispatch_authorized is False
    assert recovered.automatic_replay_authorized is False

    with sqlite3.connect(path) as connection:
        assert connection.execute("PRAGMA quick_check").fetchone() == ("ok",)
        assert connection.execute(
            "SELECT plan_id,schema_version,last_sequence "
            "FROM planner_journal_meta"
        ).fetchall() == [(_PLAN_ID, 1, 0)]
        assert connection.execute(
            "SELECT COUNT(*) FROM planner_journal_events"
        ).fetchone() == (0,)

    for candidate in (
        path,
        path.with_name(path.name + "-wal"),
        path.with_name(path.name + "-shm"),
        path.with_name(path.name + "-journal"),
    ):
        if candidate.exists():
            assert b"raw-sensitive-genesis-hard-exit-fixture" not in candidate.read_bytes()
