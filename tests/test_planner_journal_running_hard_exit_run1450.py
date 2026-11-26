"""Run1450: production Planner RUNNING commit survives a hard process exit.

Only synthetic PlanGraph values and disposable local SQLite are used. A
recovered RUNNING step remains ambiguous and grants no dispatch or replay.
"""

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
    PlannerJournalConflictError,
)

_PLAN_ID = "planner-running-hard-exit-run1450"
_PRIVATE = "raw-sensitive-planner-running-fixture-run1450"


def _steps() -> tuple[PlanStep, ...]:
    call = ToolCall(
        "fixture.root",
        "fixture.read",
        "synthetic:private",
        {"private_fixture": _PRIVATE},
    )
    return (
        PlanStep("root", call),
        PlanStep("dependent", call, ("root",)),
        PlanStep("independent", call),
    )


def _hard_exit_after_running_commit(database: str) -> None:
    path = Path(database)
    steps = _steps()
    journal = PlannerJournal(path)
    graph = journal.recover(_PLAN_ID, steps).graph
    native_connect = journal._connect

    class ExitAfterCommit:
        def __init__(self, connection: sqlite3.Connection) -> None:
            self.connection = connection

        def execute(self, statement: str, *args):
            result = self.connection.execute(statement, *args)
            if statement == "COMMIT":
                # The RUNNING event and metadata frontier are committed.
                # Exit before connection cleanup or a transition receipt.
                os._exit(76)
            return result

        def __getattr__(self, name: str):
            return getattr(self.connection, name)

    journal._connect = lambda: ExitAfterCommit(native_connect())
    journal.transition(
        _PLAN_ID,
        graph,
        "root",
        StepState.RUNNING,
        expected_revision=0,
        expected_sequence=0,
    )
    os._exit(77)


def test_running_transition_recovers_as_ambiguous_after_native_commit_exit(
    tmp_path: Path,
) -> None:
    path = tmp_path / "planner-running-native-commit-hard-exit.sqlite3"
    steps = _steps()
    initial = PlanGraph(steps)
    journal = PlannerJournal(path)
    journal.create_plan(_PLAN_ID, initial)

    process = multiprocessing.get_context("spawn").Process(
        target=_hard_exit_after_running_commit,
        args=(str(path),),
    )
    process.start()
    process.join(timeout=35)
    if process.is_alive():
        process.terminate()
        process.join(timeout=5)
        pytest.fail("Planner RUNNING hard-exit fixture did not terminate")
    assert process.exitcode == 76

    cold = PlannerJournal(path)
    recovered = cold.recover(_PLAN_ID, steps)
    statuses = recovered.graph.statuses()
    assert statuses["root"].state is StepState.RUNNING
    assert statuses["root"].revision == 1
    assert statuses["dependent"].state is StepState.PENDING
    assert statuses["dependent"].revision == 0
    assert statuses["independent"].state is StepState.PENDING
    assert statuses["independent"].revision == 0
    assert recovered.sequence == 1
    assert recovered.ambiguous_running_step_ids == ("root",)
    assert recovered.dispatch_authorized is False
    assert recovered.automatic_replay_authorized is False

    # A stale genesis graph cannot blindly repeat the committed transition.
    with pytest.raises(PlannerJournalConflictError):
        cold.transition(
            _PLAN_ID,
            initial,
            "root",
            StepState.RUNNING,
            expected_revision=0,
            expected_sequence=0,
        )
    reread = cold.recover(_PLAN_ID, steps)
    assert reread.sequence == 1
    assert reread.ambiguous_running_step_ids == ("root",)
    assert reread.dispatch_authorized is False
    assert reread.automatic_replay_authorized is False

    with sqlite3.connect(path) as connection:
        assert connection.execute("PRAGMA quick_check").fetchone() == ("ok",)
        assert connection.execute("PRAGMA user_version").fetchone() == (1,)
        assert connection.execute(
            "SELECT sequence,step_id,from_state,to_state,expected_revision "
            "FROM planner_journal_events ORDER BY sequence"
        ).fetchall() == [(1, "root", "pending", "running", 0)]
        assert connection.execute(
            "SELECT last_sequence FROM planner_journal_meta WHERE plan_id=?",
            (_PLAN_ID,),
        ).fetchone() == (1,)

    persisted = b"".join(
        item.read_bytes() for item in tmp_path.iterdir() if item.is_file()
    )
    assert _PRIVATE.encode("utf-8") not in persisted
