"""A local journal transition during Planner review invalidates the first sweep.

Only synthetic SQLite and inert PlanGraph states; no backend dispatch/replay.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from ark.agency import disconnected_planner_epoch_recheck as epoch
from ark.agency.contracts import PlanStep, StepState, ToolCall
from ark.agency.planner_journal_review import SyntheticPlanJournal

_STEP = "step_" + "1" * 16


def _running(tmp_path: Path):
    step = PlanStep(
        _STEP, ToolCall("fixture", "fixture.read", "local", {"q": 1}),
    )
    journal = SyntheticPlanJournal(tmp_path / "planner.sqlite", (step,))
    genesis = journal.recover().tail
    running = journal.append(
        _STEP, StepState.RUNNING, expected_revision=0,
        at_ms=100, retained=genesis,
    )
    return journal, genesis, running


def test_second_read_detects_committed_terminal_event_during_review(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    journal, genesis, running = _running(tmp_path)
    original_image = epoch._recovery_image
    calls: list[int] = []

    def interleave(recovery):
        image = original_image(recovery)
        calls.append(1)
        # This call is after the first original SQLite recovery snapshot,
        # but before that old result would have been returned as MATCH_AT_READ.
        if len(calls) == 3:
            journal.append(
                _STEP, StepState.FAILED, expected_revision=1,
                at_ms=110, retained=running.tail,
            )
        return image

    with monkeypatch.context() as patch:
        patch.setattr(epoch, "_recovery_image", interleave)
        with pytest.raises(
            epoch.PlannerEpochRecheckRejected,
            match="changed across local recheck sweeps",
        ):
            epoch.recheck_disconnected_planner_epoch(journal, running, genesis)

    assert len(calls) >= 4
    recovered = journal.recover(retained=genesis)
    assert recovered.tail.event_count == 2
    assert recovered.step_statuses == ((_STEP, StepState.FAILED.value, 2),)
    assert recovered.dispatch_authorized is False
    assert recovered.automatic_replay_authorized is False
    report = epoch.recheck_disconnected_planner_epoch(journal, running, genesis)
    assert report.local_freshness == "DRIFT_AT_READ"
    assert report.observed_event_count == 2
    assert report.dispatch_authorized is False
    assert report.automatic_replay_authorized is False


def test_stable_double_sweep_remains_non_authorizing(tmp_path: Path) -> None:
    journal, genesis, running = _running(tmp_path)
    report = epoch.recheck_disconnected_planner_epoch(journal, running, genesis)
    assert report.local_freshness == "MATCH_AT_READ"
    assert report.retained_event_count == 1
    assert report.observed_event_count == 1
    assert report.manual_review_required is True
    assert report.freshness_after_return_proven is False
    assert report.external_effect_proven is False
