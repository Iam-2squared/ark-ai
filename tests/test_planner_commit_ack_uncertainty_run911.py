"""Planner COMMIT acknowledgment loss is not evidence of rollback or retry.

All operations use disposable SQLite and synthetic DAG transitions only.
No backend, token, user consent, physical action or external effect exists.
"""

from __future__ import annotations

import sqlite3

import pytest

from ark.agency.contracts import PlanConflictError, PlanStep, StepState, ToolCall
from ark.agency.planner_journal_review import SyntheticPlanJournal


def _steps():
    return (
        PlanStep("root", ToolCall("fixture.read", "fixture.read", "local")),
        PlanStep("independent", ToolCall("fixture.read", "fixture.read", "local")),
    )


def _journal(path):
    return SyntheticPlanJournal(path, _steps())


class _CommitAckLoss:
    """Delegate SQLite normally but lose the acknowledgment at a chosen edge."""

    def __init__(self, connection: sqlite3.Connection, *, durable: bool):
        self.connection = connection
        self.durable = durable

    def __getattr__(self, name):
        return getattr(self.connection, name)

    def commit(self):
        if self.durable:
            self.connection.commit()
        raise OSError("disconnected synthetic COMMIT acknowledgment lost")


@pytest.mark.parametrize("durable", (False, True))
def test_uncertain_commit_requires_cold_recovery_not_automatic_retry(
    tmp_path, monkeypatch, durable,
):
    path = tmp_path / "journal.sqlite"
    journal = _journal(path)
    initial = journal.recover()
    original_connect = journal._connect

    def uncertain_connection(*, create=False):
        return _CommitAckLoss(
            original_connect(create=create), durable=durable,
        )

    with monkeypatch.context() as patch:
        patch.setattr(journal, "_connect", uncertain_connection)
        with pytest.raises(OSError, match="acknowledgment lost"):
            journal.append(
                "root", StepState.RUNNING, expected_revision=0,
                at_ms=10, retained=initial.tail,
            )

    cold = _journal(path).recover(retained=initial.tail)
    assert cold.dispatch_authorized is False
    assert cold.automatic_replay_authorized is False
    if durable:
        assert cold.tail.event_count == 1
        assert cold.ambiguous_running_steps == ("root",)
        with pytest.raises(PlanConflictError):
            _journal(path).append(
                "root", StepState.RUNNING, expected_revision=0,
                at_ms=11, retained=initial.tail,
            )
        independent = _journal(path).append(
            "independent", StepState.RUNNING, expected_revision=0,
            at_ms=12, retained=initial.tail,
        )
        assert independent.ambiguous_running_steps == ("independent", "root")
        assert independent.dispatch_authorized is False
    else:
        assert cold.tail == initial.tail
        assert cold.ambiguous_running_steps == ()
    with sqlite3.connect(path) as connection:
        expected = 2 if durable else 0
        assert connection.execute(
            "SELECT COUNT(*) FROM synthetic_plan_events"
        ).fetchone() == (expected,)
