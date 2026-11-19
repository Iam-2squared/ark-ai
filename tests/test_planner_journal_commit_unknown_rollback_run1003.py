"""Run1003: COMMIT-UNKNOWN may mean rollback, so recovery precedes retry."""

from __future__ import annotations

import sqlite3
from contextlib import closing

import pytest

import ark.agency.planner_journal as journal_module
from ark.agency.contracts import PlanStep, StepState, ToolCall
from ark.agency.planner import PlanGraph
from ark.agency.planner_journal import (
    PlannerJournal,
    PlannerJournalCommitUnknown,
    PlannerJournalNotFoundError,
)


class _FailBeforeCommitExecution:
    """Raise before SQLite receives COMMIT; close then rolls the txn back."""

    def __init__(self, connection, armed):
        self._connection = connection
        self._armed = armed

    def execute(self, statement, *args):
        if type(statement) is str and statement.strip().upper() == "COMMIT":
            if self._armed[0]:
                self._armed[0] = False
                raise sqlite3.OperationalError("synthetic COMMIT was not issued")
        return self._connection.execute(statement, *args)

    def __getattr__(self, name):
        return getattr(self._connection, name)


def _steps() -> tuple[PlanStep, ...]:
    return (
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


def _fail_before_commit_once(monkeypatch):
    real_connect = sqlite3.connect
    armed = [True]

    def connect(*args, **kwargs):
        return _FailBeforeCommitExecution(
            real_connect(*args, **kwargs),
            armed,
        )

    monkeypatch.setattr(journal_module.sqlite3, "connect", connect)
    return real_connect, armed


@pytest.mark.parametrize("operation", ("genesis", "transition"))
def test_commit_unknown_rollback_is_discovered_by_recovery_without_retry(
    tmp_path, monkeypatch, operation: str,
):
    path = tmp_path / "planner-rollback-unknown.sqlite3"
    plan_id = f"rollback-{operation}"
    steps = _steps()
    graph = PlanGraph(steps)
    journal = PlannerJournal(path)
    if operation == "transition":
        journal.create_plan(plan_id, graph)

    real_connect, armed = _fail_before_commit_once(monkeypatch)
    with pytest.raises(PlannerJournalCommitUnknown, match="COMMIT outcome is unknown"):
        if operation == "genesis":
            journal.create_plan(plan_id, graph)
        else:
            journal.transition(
                plan_id,
                graph,
                "root",
                StepState.RUNNING,
                expected_revision=0,
                expected_sequence=0,
            )
    assert armed == [False]

    if operation == "genesis":
        # The schema exists, but the genesis transaction was rolled back.
        # Absence is discovered; it is not treated as a successful plan.
        with pytest.raises(PlannerJournalNotFoundError):
            journal.recover(plan_id, steps)
        expected_meta = 0
    else:
        # The prior genesis is intact and the attempted RUNNING transition is
        # absent. No automatic retry or inferred dispatch occurs.
        recovered = journal.recover(plan_id, steps)
        assert recovered.sequence == 0
        assert recovered.ambiguous_running_step_ids == ()
        assert all(
            status.state is StepState.PENDING and status.revision == 0
            for status in recovered.graph.statuses().values()
        )
        assert recovered.dispatch_authorized is False
        assert recovered.automatic_replay_authorized is False
        assert journal.recover(plan_id, steps).sequence == 0
        expected_meta = 1

    with closing(real_connect(path)) as connection:
        assert connection.execute(
            "SELECT COUNT(*) FROM planner_journal_meta WHERE plan_id=?",
            (plan_id,),
        ).fetchone() == (expected_meta,)
        assert connection.execute(
            "SELECT COUNT(*) FROM planner_journal_events WHERE plan_id=?",
            (plan_id,),
        ).fetchone() == (0,)
