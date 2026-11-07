"""Hard-process crash boundary for a disconnected Planner WRITE journal.

No backend executes. A durable RUNNING transition stays ambiguous after
restart and cannot be downgraded to PENDING merely because its Python caller
lost the return. An uncommitted transition leaves no partial journal header.
"""

import sqlite3
import subprocess
import sys

import pytest

from ark.agency.contracts import PlanConflictError, PlanStep, StepState, ToolCall
from ark.agency.planner_journal_review import SyntheticPlanJournal

_CHILD = r"""
import os
import pathlib
import sys

import ark.agency.planner_journal_review as journal_module
from ark.agency.contracts import PlanStep, StepState, ToolCall
from ark.agency.planner_journal_review import SyntheticPlanJournal

class PostCommit:
    def __init__(self, wrapped):
        self.wrapped = wrapped

    def __getattr__(self, name):
        return getattr(self.wrapped, name)

    def commit(self):
        self.wrapped.commit()
        os._exit(62)

step = PlanStep(
    "root", ToolCall("inert", "fixture.write", "local", {"n": 1}),
)
journal = SyntheticPlanJournal(pathlib.Path(sys.argv[1]), (step,))
retained = journal.recover().tail
phase = sys.argv[2]
if phase == "before_commit":
    # Called after the event row and header were both written, but before
    # conn.commit(). A hard exit proves SQLite rolls back the full pair.
    journal_module._checked_snapshot = lambda *_args: os._exit(61)
elif phase == "after_commit":
    original_connect = journal._connect
    journal._connect = lambda *, create=False: PostCommit(
        original_connect(create=create)
    )
else:
    sys.exit("invalid planner phase")
journal.append(
    "root", StepState.RUNNING, expected_revision=0, at_ms=12,
    retained=retained,
)
sys.exit("planner child unexpectedly returned")
"""


def _journal(path):
    step = PlanStep(
        "root", ToolCall("inert", "fixture.write", "local", {"n": 1}),
    )
    return SyntheticPlanJournal(path, (step,))


@pytest.mark.parametrize(
    ("phase", "exit_code", "event_count", "running"),
    [
        ("before_commit", 61, 0, ()),
        ("after_commit", 62, 1, ("root",)),
    ],
)
def test_planner_hard_exit_keeps_journal_header_atomic_and_running_uncertain(
    tmp_path, phase, exit_code, event_count, running,
):
    path = tmp_path / "planner.sqlite3"
    _journal(path)
    finished = subprocess.run(
        [sys.executable, "-c", _CHILD, str(path), phase],
        capture_output=True, text=True, timeout=35, check=False,
    )
    assert finished.returncode == exit_code, (
        finished.returncode, finished.stdout, finished.stderr,
    )
    reopened = _journal(path)
    recovery = reopened.recover()
    assert recovery.tail.event_count == event_count
    assert recovery.ambiguous_running_steps == running
    assert recovery.dispatch_authorized is False
    assert recovery.automatic_replay_authorized is False
    with sqlite3.connect(path) as conn:
        stored_count = conn.execute(
            "SELECT event_count FROM synthetic_plan_header WHERE id=1"
        ).fetchone()[0]
        events = conn.execute(
            "SELECT seq,from_state,to_state FROM synthetic_plan_events"
        ).fetchall()
    assert stored_count == event_count == len(events)
    if event_count:
        assert events == [(1, "pending", "running")]
        # An UNKNOWN WRITE is never resumed as a new PENDING attempt.
        with pytest.raises(PlanConflictError):
            reopened.append("root", StepState.RUNNING,
                            expected_revision=0, at_ms=13)
        assert reopened.recover().tail.event_count == 1
    else:
        assert recovery.step_statuses == (("root", "pending", 0),)
        assert events == []
