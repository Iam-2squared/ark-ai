"""Run1310: Planner COMMIT-UNKNOWN is recovered, never blindly retried."""

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
    PlannerJournalConflictError,
    PlannerJournalCorruptError,
)


class _CommitThenLoseAcknowledgement:
    """Commit durably, then simulate loss of the caller's COMMIT response."""

    def __init__(self, connection, armed):
        self._connection = connection
        self._armed = armed

    def execute(self, statement, *args):
        cursor = self._connection.execute(statement, *args)
        if type(statement) is str and statement.strip().upper() == "COMMIT":
            if self._armed[0]:
                self._armed[0] = False
                raise sqlite3.OperationalError("synthetic lost COMMIT acknowledgement")
        return cursor

    def __getattr__(self, name):
        return getattr(self._connection, name)


def _inject_commit_acknowledgement_loss(monkeypatch):
    real_connect = sqlite3.connect
    armed = [True]

    def connect(*args, **kwargs):
        return _CommitThenLoseAcknowledgement(
            real_connect(*args, **kwargs),
            armed,
        )

    monkeypatch.setattr(journal_module.sqlite3, "connect", connect)
    return armed


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


def test_genesis_commit_acknowledgement_loss_is_recovered_not_retried(
    tmp_path, monkeypatch,
):
    journal = PlannerJournal(tmp_path / "planner.sqlite3")
    steps = _steps()
    graph = PlanGraph(steps)
    armed = _inject_commit_acknowledgement_loss(monkeypatch)

    with pytest.raises(PlannerJournalCommitUnknown, match="genesis COMMIT outcome is unknown"):
        journal.create_plan("unknown-genesis", graph)

    assert armed == [False]
    recovered = journal.recover("unknown-genesis", steps)
    assert recovered.sequence == 0
    assert all(
        status.state is StepState.PENDING and status.revision == 0
        for status in recovered.graph.statuses().values()
    )
    assert recovered.dispatch_authorized is False
    assert recovered.automatic_replay_authorized is False

    # The durable genesis already exists. Reissuing create is a conflict,
    # not a way to infer that the first call rolled back.
    with pytest.raises(PlannerJournalConflictError, match="already exists"):
        journal.create_plan("unknown-genesis", graph)
    assert journal.recover("unknown-genesis", steps).sequence == 0


def test_transition_commit_acknowledgement_loss_recovers_running_as_ambiguous(
    tmp_path, monkeypatch,
):
    journal = PlannerJournal(tmp_path / "planner.sqlite3")
    steps = _steps()
    graph = PlanGraph(steps)
    journal.create_plan("unknown-transition", graph)
    armed = _inject_commit_acknowledgement_loss(monkeypatch)

    with pytest.raises(
        PlannerJournalCommitUnknown,
        match="recover before any retry",
    ):
        journal.transition(
            "unknown-transition",
            graph,
            "root",
            StepState.RUNNING,
            expected_revision=0,
            expected_sequence=0,
        )

    assert armed == [False]
    recovered = journal.recover("unknown-transition", steps)
    assert recovered.sequence == 1
    assert recovered.graph.statuses()["root"].state is StepState.RUNNING
    assert recovered.ambiguous_running_step_ids == ("root",)
    assert recovered.graph.ready_steps() == ()
    assert recovered.dispatch_authorized is False
    assert recovered.automatic_replay_authorized is False

    # The pre-COMMIT graph/sequence is stale. No duplicate transition is
    # appended after the lost acknowledgement.
    with pytest.raises(PlannerJournalConflictError, match="stale"):
        journal.transition(
            "unknown-transition",
            graph,
            "root",
            StepState.CANCELLED,
            expected_revision=0,
            expected_sequence=0,
        )
    assert journal.recover("unknown-transition", steps).sequence == 1


@pytest.mark.parametrize("removed_sequence", (1, 2))
def test_recovery_rejects_interior_or_tail_event_prefix_truncation(
    tmp_path, removed_sequence: int,
):
    path = tmp_path / "planner.sqlite3"
    journal = PlannerJournal(path)
    steps = _steps()
    graph = PlanGraph(steps)
    journal.create_plan("truncated-prefix", graph)
    running = journal.transition(
        "truncated-prefix",
        graph,
        "root",
        StepState.RUNNING,
        expected_revision=0,
        expected_sequence=0,
    )
    completed = journal.transition(
        "truncated-prefix",
        running.graph,
        "root",
        StepState.SUCCEEDED,
        expected_revision=1,
        expected_sequence=1,
    )
    assert completed.receipt.sequence == 2

    with closing(sqlite3.connect(path)) as connection:
        connection.execute(
            "DELETE FROM planner_journal_events WHERE plan_id=? AND sequence=?",
            ("truncated-prefix", removed_sequence),
        )
        connection.commit()

    with pytest.raises(PlannerJournalCorruptError):
        journal.recover("truncated-prefix", steps)
