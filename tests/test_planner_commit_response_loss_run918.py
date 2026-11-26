"""Synthetic Planner commit/response ambiguity is not replay authority.

All operations are local SQLite journal transitions with inert tool
descriptors. No backend is dispatched, no physical device is accessed, and
no lost-response retry is automatically authorized.
"""

from __future__ import annotations

import sqlite3

import pytest

from ark.agency import planner_journal_review as journal
from ark.agency.contracts import PlanConflictError, PlanStep, StepState, ToolCall


def _steps():
    return (PlanStep(
        "root", ToolCall("fixture", "fixture.read", "sandbox", {"x": 1}),
    ),)


@pytest.mark.parametrize("final_state", (StepState.RUNNING, StepState.SUCCEEDED))
def test_committed_event_survives_lost_response_without_duplicate_replay(
    tmp_path, monkeypatch, final_state,
):
    path = tmp_path / "postcommit-unknown.sqlite"
    writer = journal.SyntheticPlanJournal(path, _steps())
    basis = writer.recover()
    assert basis.tail.event_count == 0
    predecessor = basis
    if final_state is StepState.SUCCEEDED:
        predecessor = writer.append(
            "root", StepState.RUNNING, expected_revision=0,
            at_ms=10, retained=basis.tail,
        )
    expected_revision = predecessor.tail.event_count
    before_count = expected_revision
    original = journal._checked_snapshot

    def lose_response_after_commit(*args, **kwargs):
        result, check = original(*args, **kwargs)

        def postcommit():
            check()
            raise RuntimeError("synthetic response lost after durable commit")

        return result, postcommit

    with monkeypatch.context() as patch:
        patch.setattr(journal, "_checked_snapshot", lose_response_after_commit)
        with pytest.raises(RuntimeError, match="response lost after durable commit"):
            writer.append(
                "root", final_state, expected_revision=expected_revision,
                at_ms=20, retained=predecessor.tail,
            )

    # The exception is not evidence of rollback: the local journal already
    # committed event+header atomically before the result callback failed.
    cold = journal.SyntheticPlanJournal(path, _steps())
    recovered = cold.recover(retained=predecessor.tail)
    assert recovered.tail.event_count == before_count + 1
    assert recovered.ambiguous_running_steps == (
        ("root",) if final_state is StepState.RUNNING else ()
    )
    assert recovered.dispatch_authorized is False
    assert recovered.automatic_replay_authorized is False
    with sqlite3.connect(path) as conn:
        count = conn.execute(
            "SELECT COUNT(*) FROM synthetic_plan_events"
        ).fetchone()[0]
        header_count = conn.execute(
            "SELECT event_count FROM synthetic_plan_header"
        ).fetchone()[0]
    assert count == header_count == before_count + 1

    # A stale expected revision is never a safe replay decision. An older
    # retained prefix can still be valid evidence, but cannot reset CAS.
    with pytest.raises(PlanConflictError):
        cold.append(
            "root", final_state, expected_revision=expected_revision,
            at_ms=30, retained=predecessor.tail,
        )
    assert cold.recover().tail == recovered.tail


def test_exception_before_commit_leaves_no_partial_journal_record(
    tmp_path, monkeypatch,
):
    path = tmp_path / "precommit-rollback.sqlite"
    writer = journal.SyntheticPlanJournal(path, _steps())
    origin = writer.recover()

    def before_commit_fault(*_args, **_kwargs):
        raise RuntimeError("synthetic failure before commit")

    with monkeypatch.context() as patch:
        patch.setattr(journal, "_checked_snapshot", before_commit_fault)
        with pytest.raises(RuntimeError, match="before commit"):
            writer.append(
                "root", StepState.RUNNING, expected_revision=0,
                at_ms=10, retained=origin.tail,
            )

    observer = journal.SyntheticPlanJournal(path, _steps())
    restored = observer.recover(retained=origin.tail)
    assert restored.tail == origin.tail
    assert restored.ambiguous_running_steps == ()
    assert restored.dispatch_authorized is False
    with sqlite3.connect(path) as conn:
        assert conn.execute(
            "SELECT COUNT(*) FROM synthetic_plan_events"
        ).fetchone()[0] == 0
