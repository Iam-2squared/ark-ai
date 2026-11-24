"""Run1236: Planner genesis COMMIT acknowledgement loss is cold-readback only."""

from __future__ import annotations

import sqlite3
from pathlib import Path

import pytest

from ark.agency.contracts import PlanStep, StepState, ToolCall
from ark.agency.planner import PlanGraph
from ark.agency.planner_journal import (
    PlannerJournal,
    PlannerJournalCommitUnknown,
    PlannerJournalConflictError,
    PlannerJournalNotFoundError,
)


def _steps() -> tuple[PlanStep, ...]:
    call = ToolCall(
        "fixture.root",
        "fixture.read",
        "synthetic:private",
        {"private_fixture": "raw-sensitive-genesis-fixture"},
    )
    return (PlanStep("root", call),)


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
                "synthetic Planner genesis COMMIT acknowledgement lost"
            )
        return self.connection.execute(statement, *args)

    def __getattr__(self, name):
        return getattr(self.connection, name)


@pytest.mark.parametrize("durable", (False, True), ids=("rolled-back", "committed"))
def test_genesis_commit_ack_loss_requires_cold_readback_without_retry(
    tmp_path: Path,
    durable: bool,
) -> None:
    path = tmp_path / "planner-genesis-commit-unknown.sqlite3"
    steps = _steps()
    graph = PlanGraph(steps)
    journal = PlannerJournal(path)
    native_connect = journal._connect
    boundaries: list[_CommitBoundary] = []

    def uncertain_connect(*, create: bool = False):
        boundary = _CommitBoundary(native_connect(create=create), durable=durable)
        boundaries.append(boundary)
        return boundary

    journal._connect = uncertain_connect
    with pytest.raises(
        PlannerJournalCommitUnknown,
        match="genesis COMMIT outcome is unknown",
    ):
        journal.create_plan("genesis-unknown-plan", graph)

    assert len(boundaries) == 1
    assert boundaries[0].commit_attempts == 1

    # Resolve the uncertain result only through a fresh journal instance.
    cold = PlannerJournal(path)
    with sqlite3.connect(path) as connection:
        assert connection.execute("PRAGMA quick_check").fetchone() == ("ok",)
        meta_count = connection.execute(
            "SELECT COUNT(*) FROM planner_journal_meta"
        ).fetchone()[0]
        event_count = connection.execute(
            "SELECT COUNT(*) FROM planner_journal_events"
        ).fetchone()[0]

    if durable:
        assert meta_count == 1
        assert event_count == 0
        recovered = cold.recover("genesis-unknown-plan", steps)
        assert recovered.sequence == 0
        assert recovered.graph.statuses()["root"].state is StepState.PENDING
        assert recovered.ambiguous_running_step_ids == ()
        assert recovered.dispatch_authorized is False
        assert recovered.automatic_replay_authorized is False
        with pytest.raises(PlannerJournalConflictError, match="already exists"):
            cold.create_plan("genesis-unknown-plan", PlanGraph(steps))
    else:
        assert meta_count == 0
        assert event_count == 0
        with pytest.raises(PlannerJournalNotFoundError):
            cold.recover("genesis-unknown-plan", steps)

    assert b"raw-sensitive-genesis-fixture" not in path.read_bytes()
    assert boundaries[0].commit_attempts == 1
