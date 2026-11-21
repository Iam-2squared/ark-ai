"""Run1034: terminal Planner COMMIT outcome is resolved only by cold readback.

A failed or lost local SQLite COMMIT acknowledgement never grants dispatch or
automatic replay. Synthetic DAG transitions only; no ToolBackend is invoked.
"""

from __future__ import annotations

import sqlite3

import pytest

from ark.agency.contracts import PlanConflictError, PlanStep, StepState, ToolCall
from ark.agency.planner_journal_review import (
    SyntheticPlanJournal,
    SyntheticPlanJournalRejected,
)


def _steps() -> tuple[PlanStep, ...]:
    call = ToolCall("fixture.read", "fixture.read", "local-only")
    return (
        PlanStep("root", call),
        PlanStep("dependent", call, ("root",)),
        PlanStep("independent", call),
    )


def _journal(path) -> SyntheticPlanJournal:
    return SyntheticPlanJournal(path, _steps())


class _CommitBoundary:
    """Inject failure immediately before or after the native SQLite COMMIT."""

    def __init__(self, connection: sqlite3.Connection, *, durable: bool) -> None:
        self.connection = connection
        self.durable = durable
        self.commit_attempts = 0
        self.native_commits = 0
        self.rollbacks = 0

    def commit(self) -> None:
        self.commit_attempts += 1
        if self.durable:
            self.connection.commit()
            self.native_commits += 1
        raise sqlite3.OperationalError("synthetic Planner COMMIT acknowledgement lost")

    def rollback(self) -> None:
        self.rollbacks += 1
        self.connection.rollback()

    def close(self) -> None:
        self.connection.close()

    def __getattr__(self, name):
        return getattr(self.connection, name)


@pytest.mark.parametrize("durable", (False, True))
def test_terminal_commit_outcome_requires_cold_recovery_and_never_replays(
    tmp_path, monkeypatch, durable: bool,
) -> None:
    path = tmp_path / "planner-terminal-commit-outcome.sqlite3"
    journal = _journal(path)
    genesis = journal.recover()
    running = journal.append(
        "root",
        StepState.RUNNING,
        expected_revision=0,
        at_ms=10,
        retained=genesis.tail,
    )

    original_connect = journal._connect
    boundaries: list[_CommitBoundary] = []

    def uncertain_connection(*, create: bool = False):
        boundary = _CommitBoundary(
            original_connect(create=create),
            durable=durable,
        )
        boundaries.append(boundary)
        return boundary

    with monkeypatch.context() as patch:
        patch.setattr(journal, "_connect", uncertain_connection)
        with pytest.raises(
            sqlite3.OperationalError,
            match="Planner COMMIT acknowledgement lost",
        ):
            journal.append(
                "root",
                StepState.FAILED,
                expected_revision=1,
                at_ms=20,
                retained=running.tail,
            )

    assert len(boundaries) == 1
    assert boundaries[0].commit_attempts == 1
    assert boundaries[0].native_commits == (1 if durable else 0)
    assert boundaries[0].rollbacks == 1

    # Reopen through a separate journal object. The pre-COMMIT rollback keeps
    # the parent RUNNING state and its child PENDING; a committed terminal
    # transition keeps FAILED + BLOCKED. Neither outcome authorizes dispatch.
    cold = _journal(path)
    recovered = cold.recover(retained=running.tail)
    statuses = {
        step_id: (state, revision)
        for step_id, state, revision in recovered.step_statuses
    }
    if durable:
        assert statuses == {
            "root": ("failed", 2),
            "dependent": ("blocked", 1),
            "independent": ("pending", 0),
        }
        assert recovered.ambiguous_running_steps == ()
        expected_events = [
            (1, "root", "pending", "running", 0, 1),
            (2, "root", "running", "failed", 1, 2),
        ]
    else:
        assert statuses == {
            "root": ("running", 1),
            "dependent": ("pending", 0),
            "independent": ("pending", 0),
        }
        assert recovered.ambiguous_running_steps == ("root",)
        expected_events = [
            (1, "root", "pending", "running", 0, 1),
        ]

    assert recovered.dispatch_authorized is False
    assert recovered.automatic_replay_authorized is False
    with sqlite3.connect(path) as connection:
        assert connection.execute(
            "SELECT seq,step_id,from_state,to_state,expected_revision,resulting_revision "
            "FROM synthetic_plan_events ORDER BY seq",
        ).fetchall() == expected_events
        assert connection.execute("PRAGMA quick_check").fetchone() == ("ok",)

    if durable:
        with pytest.raises((PlanConflictError, SyntheticPlanJournalRejected)):
            _journal(path).append(
                "root",
                StepState.FAILED,
                expected_revision=1,
                at_ms=21,
                retained=running.tail,
            )
        assert _journal(path).recover().step_statuses == recovered.step_statuses
