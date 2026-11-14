"""Run748: a lost reply after durable DAG append is not replay permission.

All actions here are inert ToolCall descriptions in a temporary local journal.
"""

from __future__ import annotations

import pytest

from ark.agency import planner_journal_review as module
from ark.agency.contracts import PlanStep, StepState, ToolCall

ROOT = "root"
CHILD = "child"
INDEPENDENT = "independent"


def _plan(tmp_path):
    steps = (
        PlanStep(ROOT, ToolCall("fixture", "offline", "local", {"n": 1})),
        PlanStep(CHILD, ToolCall("fixture", "offline", "local", {"n": 2}), (ROOT,)),
        PlanStep(INDEPENDENT, ToolCall("fixture", "offline", "local", {"n": 3})),
    )
    path = tmp_path / "postcommit-dag.sqlite3"
    journal = module.SyntheticPlanJournal(path, steps)
    return path, steps, journal, journal.recover().tail


def _fail_after_commit(monkeypatch, callback):
    original = module._checked_snapshot

    def wrap(graph, tail):
        witness, check = original(graph, tail)

        def lose_reply():
            check()
            callback.append("after_commit")
            raise module.SyntheticPlanJournalRejected("lost postcommit result")

        return witness, lose_reply

    return monkeypatch.context(), wrap


def test_dag_running_commits_even_when_receipt_callback_fails(tmp_path, monkeypatch):
    path, steps, journal, genesis = _plan(tmp_path)
    callbacks = []
    context, injected = _fail_after_commit(monkeypatch, callbacks)
    with context as patch:
        patch.setattr(module, "_checked_snapshot", injected)
        with pytest.raises(module.SyntheticPlanJournalRejected, match="postcommit"):
            journal.append(
                ROOT, StepState.RUNNING, expected_revision=0,
                at_ms=10, retained=genesis,
            )
    assert callbacks == ["after_commit"]
    restarted = module.SyntheticPlanJournal(path, steps).recover(retained=genesis)
    statuses = {key: state for key, state, _ in restarted.step_statuses}
    assert restarted.tail.event_count == 1
    assert statuses == {
        ROOT: "running", CHILD: "pending", INDEPENDENT: "pending",
    }
    assert restarted.ambiguous_running_steps == (ROOT,)
    assert restarted.dispatch_authorized is False
    assert restarted.automatic_replay_authorized is False


def test_dag_terminal_commit_unknown_propagates_block_without_replaying(
    tmp_path, monkeypatch,
):
    path, steps, journal, genesis = _plan(tmp_path)
    running = journal.append(
        ROOT, StepState.RUNNING, expected_revision=0,
        at_ms=10, retained=genesis,
    )
    assert running.ambiguous_running_steps == (ROOT,)
    callbacks = []
    context, injected = _fail_after_commit(monkeypatch, callbacks)
    with context as patch:
        patch.setattr(module, "_checked_snapshot", injected)
        with pytest.raises(module.SyntheticPlanJournalRejected, match="postcommit"):
            journal.append(
                ROOT, StepState.FAILED, expected_revision=1,
                at_ms=11, retained=genesis,
            )
    assert callbacks == ["after_commit"]
    reopened = module.SyntheticPlanJournal(path, steps)
    recovered = reopened.recover(retained=genesis)
    statuses = {key: (state, revision) for key, state, revision in recovered.step_statuses}
    assert recovered.tail.event_count == 2
    assert statuses[ROOT] == ("failed", 2)
    assert statuses[CHILD] == ("blocked", 1)
    assert statuses[INDEPENDENT] == ("pending", 0)
    assert recovered.ambiguous_running_steps == ()
    assert recovered.automatic_replay_authorized is False
    independent_running = reopened.append(
        INDEPENDENT, StepState.RUNNING, expected_revision=0,
        at_ms=12, retained=genesis,
    )
    after = module.SyntheticPlanJournal(path, steps).recover(retained=genesis)
    assert after == independent_running
    assert after.tail.event_count == 3
    assert after.ambiguous_running_steps == (INDEPENDENT,)
    assert after.automatic_replay_authorized is False
