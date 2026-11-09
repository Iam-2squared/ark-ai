"""A synthetic Planner append can commit before its result callback fails.

The caller must not retry a post-COMMIT-UNKNOWN transition from a stale
revision. These are disconnected SQLite fixture tests, not tool execution.
"""

from __future__ import annotations

import pytest

from ark.agency import planner_journal_review as journal_module
from ark.agency.contracts import PlanConflictError, PlanStep, StepState, ToolCall


def _journal(tmp_path):
    return journal_module.SyntheticPlanJournal(
        tmp_path / "plan.sqlite3",
        (PlanStep("root", ToolCall("fixture", "offline", "local", {"n": 1})),),
    )


def test_postcommit_result_callback_failure_does_not_undo_durable_running(
    tmp_path, monkeypatch,
):
    journal = _journal(tmp_path)
    before = journal.recover()
    original = journal_module._checked_snapshot
    callbacks = []

    def fail_after_commit(graph, tail):
        result, check_result = original(graph, tail)

        def delayed_failure():
            check_result()
            callbacks.append("after_commit")
            raise journal_module.SyntheticPlanJournalRejected(
                "synthetic postcommit result callback failure"
            )

        return result, delayed_failure

    with monkeypatch.context() as patch:
        patch.setattr(journal_module, "_checked_snapshot", fail_after_commit)
        with pytest.raises(
            journal_module.SyntheticPlanJournalRejected, match="postcommit",
        ):
            journal.append(
                "root", StepState.RUNNING,
                expected_revision=0, at_ms=11, retained=before.tail,
            )
    assert callbacks == ["after_commit"]

    # A Python exception after a successful COMMIT is not rollback evidence.
    after = _journal(tmp_path).recover(retained=before.tail)
    assert after.tail.event_count == 1
    assert after.ambiguous_running_steps == ("root",)
    assert after.dispatch_authorized is False
    assert after.automatic_replay_authorized is False
    with pytest.raises(PlanConflictError, match="revision"):
        _journal(tmp_path).append(
            "root", StepState.RUNNING, expected_revision=0, at_ms=12,
        )
    assert _journal(tmp_path).recover().tail == after.tail


def test_precommit_result_construction_failure_leaves_prior_head(
    tmp_path, monkeypatch,
):
    journal = _journal(tmp_path)
    before = journal.recover()

    def fail_before_commit(_graph, _tail):
        raise journal_module.SyntheticPlanJournalRejected(
            "synthetic precommit result callback failure"
        )

    with monkeypatch.context() as patch:
        patch.setattr(journal_module, "_checked_snapshot", fail_before_commit)
        with pytest.raises(
            journal_module.SyntheticPlanJournalRejected, match="precommit",
        ):
            journal.append(
                "root", StepState.RUNNING,
                expected_revision=0, at_ms=11, retained=before.tail,
            )
    after = _journal(tmp_path).recover(retained=before.tail)
    assert after.tail == before.tail
    assert after.ambiguous_running_steps == ()
    assert after.automatic_replay_authorized is False
