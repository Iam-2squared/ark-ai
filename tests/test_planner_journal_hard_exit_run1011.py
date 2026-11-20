"""Hard-process crash boundaries for the durable Planner journal.

The child exits at the SQLite COMMIT boundary. No tool backend is called and
no external action is inferred from a recovered RUNNING transition.
"""

from __future__ import annotations

import sqlite3
import subprocess
import sys
from contextlib import closing

import pytest

from ark.agency.contracts import PlanStep, StepState, ToolCall
from ark.agency.planner import PlanGraph
from ark.agency.planner_journal import (
    PlannerJournal,
    PlannerJournalConflictError,
    PlannerJournalNotFoundError,
)

_CHILD = r"""
import os
import pathlib
import sqlite3
import sys

from ark.agency.contracts import PlanStep, StepState, ToolCall
from ark.agency.planner import PlanGraph
from ark.agency.planner_journal import PlannerJournal

path = pathlib.Path(sys.argv[1])
operation = sys.argv[2]
plan_id = sys.argv[3]
phase = sys.argv[4]

steps = (
    PlanStep(
        "root",
        ToolCall("fixture.root", "fixture.read", "synthetic:private", {"value": "root"}),
    ),
    PlanStep(
        "child",
        ToolCall("fixture.child", "fixture.read", "synthetic:private", {"value": "child"}),
        ("root",),
    ),
)

armed = [False]
real_connect = sqlite3.connect


class ExitAtCommit:
    def __init__(self, connection):
        self._connection = connection

    def execute(self, statement, *args):
        is_commit = (
            type(statement) is str and statement.strip().upper() == "COMMIT"
        )
        if armed[0] and is_commit and phase == "before_commit":
            os._exit(71)
        cursor = self._connection.execute(statement, *args)
        if armed[0] and is_commit and phase == "after_commit":
            os._exit(72)
        return cursor

    def __getattr__(self, name):
        return getattr(self._connection, name)


def connect(*args, **kwargs):
    return ExitAtCommit(real_connect(*args, **kwargs))


sqlite3.connect = connect
journal = PlannerJournal(path)
armed[0] = True
graph = PlanGraph(steps)

if operation == "genesis":
    journal.create_plan(plan_id, graph)
elif operation == "transition":
    journal.transition(
        plan_id,
        graph,
        "root",
        StepState.RUNNING,
        expected_revision=0,
        expected_sequence=0,
    )
else:
    sys.exit("invalid operation")

sys.exit("Planner journal call unexpectedly returned")
"""


def _steps() -> tuple[PlanStep, ...]:
    return (
        PlanStep(
            "root",
            ToolCall(
                "fixture.root",
                "fixture.read",
                "synthetic:private",
                {"value": "root"},
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


@pytest.mark.parametrize(
    ("operation", "phase", "exit_code"),
    [
        ("genesis", "before_commit", 71),
        ("genesis", "after_commit", 72),
        ("transition", "before_commit", 71),
        ("transition", "after_commit", 72),
    ],
)
def test_planner_journal_hard_exit_at_commit_requires_cold_recovery(
    tmp_path, operation: str, phase: str, exit_code: int,
) -> None:
    path = tmp_path / "planner-hard-exit.sqlite3"
    plan_id = f"hard-exit-{operation}-{phase}"
    steps = _steps()
    graph = PlanGraph(steps)
    journal = PlannerJournal(path)
    if operation == "transition":
        journal.create_plan(plan_id, graph)

    finished = subprocess.run(
        [sys.executable, "-c", _CHILD, str(path), operation, plan_id, phase],
        capture_output=True,
        text=True,
        timeout=35,
        check=False,
    )
    assert finished.returncode == exit_code, (
        finished.returncode, finished.stdout, finished.stderr,
    )

    reopened = PlannerJournal(path)
    if operation == "genesis" and phase == "before_commit":
        with pytest.raises(PlannerJournalNotFoundError):
            reopened.recover(plan_id, steps)
        expected_meta = 0
        expected_events = 0
    else:
        recovery = reopened.recover(plan_id, steps)
        assert recovery.dispatch_authorized is False
        assert recovery.automatic_replay_authorized is False
        if operation == "genesis":
            assert recovery.sequence == 0
            assert recovery.ambiguous_running_step_ids == ()
            assert all(
                status.state is StepState.PENDING and status.revision == 0
                for status in recovery.graph.statuses().values()
            )
            expected_meta = 1
            expected_events = 0
        elif phase == "before_commit":
            assert recovery.sequence == 0
            assert recovery.ambiguous_running_step_ids == ()
            assert recovery.graph.statuses()["root"].state is StepState.PENDING
            assert recovery.graph.statuses()["root"].revision == 0
            expected_meta = 1
            expected_events = 0
        else:
            assert recovery.sequence == 1
            assert recovery.ambiguous_running_step_ids == ("root",)
            assert recovery.graph.statuses()["root"].state is StepState.RUNNING
            assert recovery.graph.ready_steps() == ()
            expected_meta = 1
            expected_events = 1
            with pytest.raises(PlannerJournalConflictError):
                reopened.transition(
                    plan_id,
                    graph,
                    "root",
                    StepState.CANCELLED,
                    expected_revision=0,
                    expected_sequence=0,
                )
            assert reopened.recover(plan_id, steps).sequence == 1

    with closing(sqlite3.connect(path)) as connection:
        assert connection.execute("PRAGMA quick_check").fetchall() == [("ok",)]
        assert connection.execute(
            "SELECT COUNT(*) FROM planner_journal_meta WHERE plan_id=?",
            (plan_id,),
        ).fetchone() == (expected_meta,)
        assert connection.execute(
            "SELECT COUNT(*) FROM planner_journal_events WHERE plan_id=?",
            (plan_id,),
        ).fetchone() == (expected_events,)
        if expected_meta:
            assert connection.execute(
                "SELECT last_sequence FROM planner_journal_meta WHERE plan_id=?",
                (plan_id,),
            ).fetchone() == (expected_events,)
