"""Run1149: Planner journal quarantines ambiguous SQLite COMMIT outcomes."""

from __future__ import annotations

import subprocess
import sys

import pytest


@pytest.mark.parametrize("durable", (False, True))
def test_planner_append_commit_ack_loss_preserves_atomic_recovery(
    tmp_path,
    durable: bool,
) -> None:
    database = tmp_path / "planner-commit-unknown.sqlite3"
    script = r"""
import sqlite3
from pathlib import Path

DATABASE = Path(__DATABASE__)
DURABLE = __DURABLE__
TARGET_URI = DATABASE.resolve().as_uri() + "?mode=rw"
armed = False
commit_attempts = 0
native_connect = sqlite3.connect


class CommitBoundary:
    def __init__(self, connection):
        self.connection = connection

    def commit(self):
        global commit_attempts
        commit_attempts += 1
        if DURABLE:
            self.connection.commit()
        else:
            self.connection.rollback()
        raise sqlite3.OperationalError(
            "synthetic Planner COMMIT acknowledgement lost"
        )

    def rollback(self):
        self.connection.rollback()

    def close(self):
        self.connection.close()

    def __getattr__(self, name):
        return getattr(self.connection, name)


def controlled_connect(database, *args, **kwargs):
    connection = native_connect(database, *args, **kwargs)
    if armed and database == TARGET_URI:
        return CommitBoundary(connection)
    return connection


# Keep the injected factory stable; arm only the append's exact read/write URI.
sqlite3.connect = controlled_connect

from ark.agency.contracts import PlanStep, PlanConflictError, StepState, ToolCall
from ark.agency.planner_journal_review import SyntheticPlanJournal

step = PlanStep(
    "root", ToolCall("inert", "fixture.write", "local", {"n": 1}),
)
journal = SyntheticPlanJournal(DATABASE, (step,))
retained = journal.recover().tail

armed = True
try:
    journal.append(
        "root", StepState.RUNNING, expected_revision=0, at_ms=12,
        retained=retained,
    )
except sqlite3.OperationalError as exc:
    assert "COMMIT acknowledgement lost" in str(exc)
else:
    raise AssertionError("ambiguous Planner COMMIT unexpectedly returned")
finally:
    armed = False

# append must make one COMMIT attempt only; it never retries the transition.
assert commit_attempts == 1
reopened = SyntheticPlanJournal(DATABASE, (step,))
recovery = reopened.recover()

if DURABLE:
    assert recovery.tail.event_count == 1
    assert recovery.step_statuses == (("root", "running", 1),)
    assert recovery.ambiguous_running_steps == ("root",)
    assert recovery.dispatch_authorized is False
    assert recovery.automatic_replay_authorized is False

    # The persisted RUNNING transition cannot be replayed from the stale
    # genesis revision after its COMMIT acknowledgement was lost.
    try:
        reopened.append(
            "root", StepState.RUNNING, expected_revision=0, at_ms=13,
        )
    except PlanConflictError:
        pass
    else:
        raise AssertionError("durable ambiguous Planner COMMIT was replayed")
    assert reopened.recover().tail.event_count == 1
    expected_events = [(1, "pending", "running")]
else:
    assert recovery.tail.event_count == 0
    assert recovery.step_statuses == (("root", "pending", 0),)
    assert recovery.ambiguous_running_steps == ()
    expected_events = []

with native_connect(DATABASE) as connection:
    header_count = connection.execute(
        "SELECT event_count FROM synthetic_plan_header WHERE id=1"
    ).fetchone()[0]
    events = connection.execute(
        "SELECT seq,from_state,to_state FROM synthetic_plan_events"
    ).fetchall()

assert header_count == len(events) == recovery.tail.event_count
assert events == expected_events
assert commit_attempts == 1
"""
    script = (
        script
        .replace("__DATABASE__", repr(str(database)))
        .replace("__DURABLE__", repr(durable))
    )
    result = subprocess.run(
        [sys.executable, "-c", script],
        capture_output=True,
        text=True,
        timeout=90,
        check=False,
    )
    assert result.returncode == 0, result.stdout + result.stderr
