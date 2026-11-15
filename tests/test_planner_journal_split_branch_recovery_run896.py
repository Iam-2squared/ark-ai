"""Durable disconnected Planner fan-in with one unresolved RUNNING branch.

Synthetic SQLite only. A cold replay, independent branch completion, or
terminal cascade is never approval to redispatch an ambiguous tool call.
"""

import pytest

from ark.agency.contracts import PlanConflictError, PlanStep, StepState, ToolCall
from ark.agency.planner_journal_review import SyntheticPlanJournal


def _steps() -> tuple[PlanStep, ...]:
    def step(name, dependencies=()):
        return PlanStep(
            name,
            ToolCall("fixture.inspect", "fixture.read", "synthetic", {"id": name}),
            dependencies,
        )

    return (
        step("alpha"),
        step("alpha_child", ("alpha",)),
        step("beta"),
        step("join", ("alpha_child", "beta")),
        step("spare"),
    )


def _state(recovery):
    return {
        name: (state, revision)
        for name, state, revision in recovery.step_statuses
    }


def test_restart_unknown_branch_blocks_fanin_but_not_independent_progress(tmp_path):
    path = tmp_path / "split-branch.sqlite"
    initial = SyntheticPlanJournal(path, _steps())
    genesis = initial.recover().tail
    first = initial.append(
        "alpha", StepState.RUNNING, expected_revision=0, at_ms=10,
        retained=genesis,
    )
    cold = SyntheticPlanJournal(path, _steps())
    assert cold.recover(retained=genesis).ambiguous_running_steps == ("alpha",)
    cold.append(
        "beta", StepState.RUNNING, expected_revision=0, at_ms=20,
        retained=genesis,
    )
    cold.append(
        "beta", StepState.SUCCEEDED, expected_revision=1, at_ms=21,
        retained=genesis,
    )
    snapshot = SyntheticPlanJournal(path, _steps()).recover(retained=first.tail)
    assert snapshot.ambiguous_running_steps == ("alpha",)
    assert _state(snapshot) == {
        "alpha": ("running", 1),
        "alpha_child": ("pending", 0),
        "beta": ("succeeded", 2),
        "join": ("pending", 0),
        "spare": ("pending", 0),
    }
    assert snapshot.dispatch_authorized is False
    assert snapshot.automatic_replay_authorized is False
    with pytest.raises(PlanConflictError, match="dependencies"):
        cold.append(
            "join", StepState.RUNNING, expected_revision=0, at_ms=22,
            retained=genesis,
        )
    with pytest.raises(PlanConflictError):
        cold.append(
            "alpha", StepState.RUNNING, expected_revision=0, at_ms=22,
            retained=genesis,
        )
    assert cold.recover(retained=genesis) == snapshot
    cold.append("spare", StepState.RUNNING, expected_revision=0, at_ms=23)
    later = SyntheticPlanJournal(path, _steps()).recover(retained=snapshot.tail)
    assert later.ambiguous_running_steps == ("alpha",)
    assert _state(later)["spare"] == ("running", 1)
    assert _state(later)["join"] == ("pending", 0)


def test_manual_failure_quarantines_fanin_without_replaying_other_running_branch(
    tmp_path,
):
    path = tmp_path / "terminal-branch.sqlite"
    ledger = SyntheticPlanJournal(path, _steps())
    ledger.append("alpha", StepState.RUNNING, expected_revision=0, at_ms=1)
    ledger.append("beta", StepState.RUNNING, expected_revision=0, at_ms=2)
    failed = ledger.append(
        "alpha", StepState.FAILED, expected_revision=1, at_ms=3,
    )
    cold = SyntheticPlanJournal(path, _steps())
    snapshot = cold.recover(retained=failed.tail)
    assert _state(snapshot) == {
        "alpha": ("failed", 2),
        "alpha_child": ("blocked", 1),
        "beta": ("running", 1),
        "join": ("blocked", 1),
        "spare": ("pending", 0),
    }
    assert snapshot.ambiguous_running_steps == ("beta",)
    assert snapshot.automatic_replay_authorized is False
    with pytest.raises(PlanConflictError):
        cold.append(
            "join", StepState.RUNNING, expected_revision=1, at_ms=4,
            retained=failed.tail,
        )
    cold.append(
        "beta", StepState.SUCCEEDED, expected_revision=1, at_ms=5,
        retained=failed.tail,
    )
    latest = SyntheticPlanJournal(path, _steps()).recover(retained=failed.tail)
    assert _state(latest)["join"] == ("blocked", 1)
    assert latest.ambiguous_running_steps == ()
    assert latest.dispatch_authorized is False
