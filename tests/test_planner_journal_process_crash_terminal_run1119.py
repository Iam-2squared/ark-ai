"""Run1119: a hard process exit never turns a Planner RUNNING step into a retry."""

from __future__ import annotations

import subprocess
import sys
import textwrap
import sqlite3

import pytest

from ark.agency.contracts import PlanStep, StepState, ToolCall
from ark.agency.planner_journal_review import SyntheticPlanJournal


def _steps() -> tuple[PlanStep, ...]:
    call = ToolCall("fixture.read", "fixture.read", "local-only")
    return (
        PlanStep("root", call),
        PlanStep("dependent", call, ("root",)),
        PlanStep("independent", call),
    )


def _journal(path) -> SyntheticPlanJournal:
    return SyntheticPlanJournal(path, _steps())


@pytest.mark.parametrize(
    ("phase", "exit_code", "expected_root", "expected_dependent", "ambiguous"),
    (
        ("before", 73, "running", "pending", ("root",)),
        ("after", 74, "failed", "blocked", ()),
    ),
)
def test_terminal_transition_hard_exit_is_resolved_only_by_cold_recovery(
    tmp_path,
    phase: str,
    exit_code: int,
    expected_root: str,
    expected_dependent: str,
    ambiguous: tuple[str, ...],
) -> None:
    path = tmp_path / f"planner-hard-exit-{phase}.sqlite3"
    journal = _journal(path)
    genesis = journal.recover()
    running = journal.append(
        "root",
        StepState.RUNNING,
        expected_revision=0,
        at_ms=10,
        retained=genesis.tail,
    )

    child = textwrap.dedent(
        """
        import os
        import sys

        from ark.agency.contracts import PlanStep, StepState, ToolCall
        from ark.agency.planner_journal_review import SyntheticPlanJournal

        path = sys.argv[1]
        phase = sys.argv[2]
        call = ToolCall("fixture.read", "fixture.read", "local-only")
        steps = (
            PlanStep("root", call),
            PlanStep("dependent", call, ("root",)),
            PlanStep("independent", call),
        )
        journal = SyntheticPlanJournal(path, steps)
        recovered = journal.recover()

        class ExitAtCommit:
            def __init__(self, connection):
                self.connection = connection

            def commit(self):
                if phase == "after":
                    self.connection.commit()
                    os._exit(74)
                os._exit(73)

            def __getattr__(self, name):
                return getattr(self.connection, name)

        original_connect = journal._connect

        def crash_connect(*, create=False):
            return ExitAtCommit(original_connect(create=create))

        journal._connect = crash_connect
        journal.append(
            "root",
            StepState.FAILED,
            expected_revision=1,
            at_ms=20,
            retained=recovered.tail,
        )
        os._exit(99)
        """
    )
    completed = subprocess.run(
        [sys.executable, "-c", child, str(path), phase],
        capture_output=True,
        text=True,
        timeout=30,
        check=False,
    )
    assert completed.returncode == exit_code, completed.stderr

    cold = _journal(path)
    recovered = cold.recover(retained=running.tail)
    statuses = {
        step_id: (state, revision)
        for step_id, state, revision in recovered.step_statuses
    }
    assert statuses == {
        "root": (expected_root, 1 if phase == "before" else 2),
        "dependent": (expected_dependent, 0 if phase == "before" else 1),
        "independent": ("pending", 0),
    }
    assert recovered.ambiguous_running_steps == ambiguous
    assert recovered.dispatch_authorized is False
    assert recovered.automatic_replay_authorized is False

    expected_events = [
        (1, "root", "pending", "running", 0, 1),
    ]
    if phase == "after":
        expected_events.append((2, "root", "running", "failed", 1, 2))
    with sqlite3.connect(path) as connection:
        assert connection.execute(
            "SELECT seq,step_id,from_state,to_state,expected_revision,resulting_revision "
            "FROM synthetic_plan_events ORDER BY seq",
        ).fetchall() == expected_events
        assert connection.execute("PRAGMA quick_check").fetchone() == ("ok",)
