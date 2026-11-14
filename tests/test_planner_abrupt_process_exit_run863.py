"""Disposable Planner recovery after interpreter termination without Python cleanup.

SQLite-local journal state is not an external tool effect or permission. No
ToolBackend is instantiated and no automatic replay is authorized by recovery.
"""

from __future__ import annotations

import os
from multiprocessing import get_context
from pathlib import Path

import pytest

from ark.agency.contracts import PlanConflictError, PlanStep, StepState, ToolCall
from ark.agency.planner_journal_review import SyntheticPlanJournal


def _steps() -> tuple[PlanStep, ...]:
    return (
        PlanStep("root", ToolCall("fixture", "offline", "local", {"n": 1})),
        PlanStep("child", ToolCall("fixture", "offline", "local", {"n": 2}), ("root",)),
        PlanStep("other", ToolCall("fixture", "offline", "local", {"n": 3})),
    )


def _commit_then_exit(path: str, final: StepState) -> None:
    journal = SyntheticPlanJournal(Path(path), _steps())
    first = journal.append("root", StepState.RUNNING, expected_revision=0, at_ms=100)
    if final is not StepState.RUNNING:
        journal.append(
            "root", final, expected_revision=1, at_ms=101, retained=first.tail,
        )
    # Simulate sudden process death *after* SQLite has committed. Do not
    # run a Python finally block or deliver a receipt to the parent.
    os._exit(0)


@pytest.mark.parametrize(
    "last",
    (StepState.RUNNING, StepState.SUCCEEDED, StepState.FAILED, StepState.CANCELLED),
)
def test_recovery_after_abrupt_worker_exit_never_grants_dispatch(
    tmp_path: Path, last: StepState,
) -> None:
    path = tmp_path / "interpreter-exit.sqlite"
    genesis = SyntheticPlanJournal(path, _steps()).recover().tail
    child = get_context("spawn").Process(
        target=_commit_then_exit, args=(str(path), last),
    )
    try:
        child.start()
        child.join(timeout=35)
        assert child.exitcode == 0
    finally:
        if child.is_alive():
            child.terminate()
            child.join(timeout=5)

    recovered = SyntheticPlanJournal(path, _steps()).recover(retained=genesis)
    expected_count = 1 if last is StepState.RUNNING else 2
    assert recovered.tail.event_count == expected_count
    assert recovered.dispatch_authorized is False
    assert recovered.automatic_replay_authorized is False
    states = {
        name: (status, revision)
        for name, status, revision in recovered.step_statuses
    }
    assert states["root"] == (last.value, expected_count)
    assert states["other"] == ("pending", 0)
    assert states["child"] == (
        ("blocked", 1) if last in (StepState.FAILED, StepState.CANCELLED)
        else ("pending", 0)
    )
    assert recovered.ambiguous_running_steps == (
        ("root",) if last is StepState.RUNNING else ()
    )
    reopened = SyntheticPlanJournal(path, _steps())
    assert reopened.recover(retained=genesis) == recovered
    with pytest.raises(PlanConflictError):
        reopened.append(
            "root", StepState.RUNNING, expected_revision=0,
            at_ms=102, retained=genesis,
        )
