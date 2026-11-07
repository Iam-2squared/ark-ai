"""Mixed terminal and unresolved RUNNING branches survive SQLite restart.

Synthetic Planner only: no registered backend is invoked and recovered RUNNING
is UNKNOWN, never an invitation to retry or a proven external outcome.
"""

from pathlib import Path

import pytest

from ark.agency.contracts import PlanConflictError, PlanStep, StepState, ToolCall
from ark.agency.planner_journal_review import SyntheticPlanJournal


def _steps():
    def step(name, *dependencies):
        return PlanStep(
            name, ToolCall("fixture", "cap", "local", {"step": name}),
            dependencies,
        )
    return (
        step("root"),
        step("child", "root"),
        step("grandchild", "child"),
        step("parallel"),
        step("parallel_child", "parallel"),
    )


def _journal(path: Path):
    return SyntheticPlanJournal(path, _steps())


@pytest.mark.parametrize("terminal", (StepState.FAILED, StepState.CANCELLED))
def test_mixed_terminal_branch_and_running_branch_restart_quarantines_only_running(
    tmp_path: Path, terminal,
):
    path = tmp_path / "plans.sqlite"
    journal = _journal(path)
    journal.append("root", StepState.RUNNING, expected_revision=0, at_ms=10)
    journal.append("parallel", StepState.RUNNING, expected_revision=0, at_ms=11)
    final = journal.append("root", terminal, expected_revision=1, at_ms=12)
    assert final.tail.event_count == 3
    assert final.ambiguous_running_steps == ("parallel",)
    assert dict((name, (state, revision)) for name, state, revision
                in final.step_statuses) == {
        "root": (terminal.value, 2),
        "child": ("blocked", 1),
        "grandchild": ("blocked", 1),
        "parallel": ("running", 1),
        "parallel_child": ("pending", 0),
    }

    # Reconstruct a fresh journal from the same local data and independent
    # retained witness; a RUNNING occurrence must NOT become a ready step.
    reloaded = _journal(path)
    recovered = reloaded.recover(retained=final.tail)
    assert recovered == final
    assert recovered.dispatch_authorized is False
    assert recovered.automatic_replay_authorized is False
    with pytest.raises(PlanConflictError, match="invalid transition"):
        reloaded.append(
            "parallel", StepState.RUNNING, expected_revision=1, at_ms=13,
        )
    assert reloaded.recover(retained=final.tail) == final


def test_explicit_block_of_root_preserves_unrelated_running_unknown(tmp_path: Path):
    path = tmp_path / "plans.sqlite"
    journal = _journal(path)
    journal.append("parallel", StepState.RUNNING, expected_revision=0, at_ms=10)
    final = journal.append("root", StepState.BLOCKED, expected_revision=0, at_ms=11)
    assert final.ambiguous_running_steps == ("parallel",)
    assert dict((name, state) for name, state, _rev in final.step_statuses) == {
        "root": "blocked",
        "child": "blocked",
        "grandchild": "blocked",
        "parallel": "running",
        "parallel_child": "pending",
    }
    assert _journal(path).recover(retained=final.tail) == final


def test_independent_terminal_completion_does_not_resolve_other_unknown(
    tmp_path: Path,
):
    path = tmp_path / "plans.sqlite"
    journal = _journal(path)
    journal.append("root", StepState.RUNNING, expected_revision=0, at_ms=2)
    journal.append("parallel", StepState.RUNNING, expected_revision=0, at_ms=3)
    final = journal.append(
        "parallel", StepState.SUCCEEDED, expected_revision=1, at_ms=4,
    )
    assert final.ambiguous_running_steps == ("root",)
    assert final.dispatch_authorized is False
    assert final.automatic_replay_authorized is False
    assert _journal(path).recover(retained=final.tail) == final
