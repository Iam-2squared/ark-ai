"""One-store Planner epoch recheck is never a cross-store execution lease."""

from __future__ import annotations

import sqlite3
from dataclasses import replace
from pathlib import Path

import pytest

from ark.agency.contracts import PlanStep, StepState, ToolCall
from ark.agency.disconnected_planner_epoch_recheck import (
    PlannerEpochRecheckRejected,
    recheck_disconnected_planner_epoch,
)
from ark.agency.planner_journal_review import SyntheticPlanJournal

_WRITE = "step_" + "1" * 16
_READ = "step_" + "2" * 16


def _setup(tmp_path: Path):
    steps = (
        PlanStep(_WRITE, ToolCall("writer", "fixture.write", "local", {"v": 1})),
        PlanStep(
            _READ, ToolCall("reader", "fixture.read", "local", {"q": 1}),
            (_WRITE,),
        ),
    )
    path = tmp_path / "planner.sqlite"
    journal = SyntheticPlanJournal(path, steps)
    genesis = journal.recover().tail
    running = journal.append(
        _WRITE, StepState.RUNNING, expected_revision=0,
        at_ms=100, retained=genesis,
    )
    return journal, genesis, running, path


def test_unchanged_recovery_matches_only_at_local_read(tmp_path: Path) -> None:
    journal, genesis, running, _path = _setup(tmp_path)
    review = recheck_disconnected_planner_epoch(journal, running, genesis)
    assert review.local_freshness == "MATCH_AT_READ"
    assert review.plan_id == running.tail.topology_digest
    assert review.retained_event_count == 1
    assert review.observed_event_count == 1
    assert review.dispatch_authorized is False
    assert review.automatic_replay_authorized is False
    assert review.freshness_after_return_proven is False
    assert review.external_effect_proven is False
    assert review.manual_review_required is True


def test_subsequent_terminal_commit_marks_prior_running_snapshot_stale(
    tmp_path: Path,
) -> None:
    journal, genesis, running, _path = _setup(tmp_path)
    local_match = recheck_disconnected_planner_epoch(journal, running, genesis)
    assert local_match.local_freshness == "MATCH_AT_READ"
    journal.append(
        _WRITE, StepState.FAILED, expected_revision=1,
        at_ms=110, retained=running.tail,
    )
    stale = recheck_disconnected_planner_epoch(journal, running, genesis)
    assert stale.local_freshness == "DRIFT_AT_READ"
    assert stale.retained_event_count == 1
    assert stale.observed_event_count == 2
    assert stale.dispatch_authorized is False
    assert stale.automatic_replay_authorized is False
    assert stale.freshness_after_return_proven is False
    assert stale.manual_review_required is True
    # Prior MATCH_AT_READ cannot be promoted to a durable write lease.
    assert local_match.freshness_after_return_proven is False


def test_false_retained_prefix_is_refused_not_silently_refreshed(
    tmp_path: Path,
) -> None:
    journal, genesis, running, _path = _setup(tmp_path)
    forged = replace(genesis, event_hash="pevt_" + "f" * 64)
    with pytest.raises(PlannerEpochRecheckRejected):
        recheck_disconnected_planner_epoch(journal, running, forged)


def test_corrupted_local_journal_is_not_treated_as_absent_or_current(
    tmp_path: Path,
) -> None:
    journal, genesis, running, path = _setup(tmp_path)
    with sqlite3.connect(path) as conn:
        conn.execute(
            "UPDATE synthetic_plan_header SET tail_hash=? WHERE id=1",
            ("pevt_" + "f" * 64,),
        )
    with pytest.raises(PlannerEpochRecheckRejected):
        recheck_disconnected_planner_epoch(journal, running, genesis)


def test_replaced_replay_method_refused_before_open(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    journal, genesis, running, _path = _setup(tmp_path)
    invoked: list[str] = []

    def unsafe_replay(self, *, retained=None):
        invoked.append("called")
        return running

    monkeypatch.setattr(SyntheticPlanJournal, "recover", unsafe_replay)
    with pytest.raises(PlannerEpochRecheckRejected):
        recheck_disconnected_planner_epoch(journal, running, genesis)
    assert invoked == []
