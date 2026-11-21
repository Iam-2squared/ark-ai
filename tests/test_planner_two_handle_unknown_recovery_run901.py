"""Offline Planner multi-handle recovery and fail-closed ambiguity cases.

Journal-only synthetic transitions: no real backend, approval, replay or
external occurrence. These tests do not authorize a WRITE.
"""

import sqlite3

import pytest

from ark.agency.contracts import PlanConflictError, PlanStep, StepState, ToolCall
from ark.agency.planner_journal_review import SyntheticPlanJournal


def _two_root_steps():
    return (
        PlanStep("root-a", ToolCall("fixture", "local.read", "sandbox", {"i": 1})),
        PlanStep("root-b", ToolCall("fixture", "local.write", "sandbox", {"i": 2})),
    )


def _journal(path):
    return SyntheticPlanJournal(path, _two_root_steps())


def test_two_handles_reject_stale_cas_without_additional_event(tmp_path):
    path = tmp_path / "planner.sqlite3"
    first = _journal(path)
    second = _journal(path)
    genesis = second.recover().tail
    winner = first.append(
        "root-a", StepState.RUNNING, expected_revision=0, at_ms=10,
    )
    with pytest.raises(PlanConflictError):
        second.append(
            "root-a", StepState.RUNNING, expected_revision=0, at_ms=11,
            retained=genesis,
        )
    assert _journal(path).recover().tail == winner.tail
    with sqlite3.connect(path) as conn:
        assert conn.execute(
            "SELECT COUNT(*) FROM synthetic_plan_events"
        ).fetchone() == (1,)


def test_restarted_two_running_roots_remain_distinct_unknown_occurrences(tmp_path):
    path = tmp_path / "planner.sqlite3"
    writer = _journal(path)
    first = writer.append(
        "root-a", StepState.RUNNING, expected_revision=0, at_ms=10,
    )
    second = writer.append(
        "root-b", StepState.RUNNING, expected_revision=0, at_ms=11,
        retained=first.tail,
    )
    restarted = _journal(path)
    recovered = restarted.recover(retained=first.tail)
    assert recovered.tail == second.tail
    assert recovered.ambiguous_running_steps == ("root-a", "root-b")
    assert recovered.dispatch_authorized is False
    assert recovered.automatic_replay_authorized is False
    with pytest.raises(PlanConflictError):
        restarted.append(
            "root-b", StepState.RUNNING, expected_revision=0, at_ms=12,
            retained=second.tail,
        )
    assert restarted.recover().tail == second.tail


def test_independent_terminal_resolution_does_not_replay_other_unknown(tmp_path):
    path = tmp_path / "planner.sqlite3"
    journal = _journal(path)
    journal.append("root-a", StepState.RUNNING, expected_revision=0, at_ms=1)
    journal.append("root-b", StepState.RUNNING, expected_revision=0, at_ms=2)
    restarted = _journal(path)
    restarted.append("root-a", StepState.FAILED, expected_revision=1, at_ms=3)
    final = restarted.recover()
    assert final.ambiguous_running_steps == ("root-b",)
    assert ("root-a", "failed", 2) in final.step_statuses
    assert ("root-b", "running", 1) in final.step_statuses
    assert final.automatic_replay_authorized is False
    assert final.dispatch_authorized is False
