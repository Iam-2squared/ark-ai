"""Detached Planner state images must match their own canonical tail digest.

Disposable local SQLite only. Matching evidence is never dispatch authority.
"""

from dataclasses import replace

import pytest

from ark.agency.contracts import PlanStep, StepState, ToolCall
from ark.agency.disconnected_planner_epoch_recheck import (
    PlannerEpochRecheckRejected,
    recheck_disconnected_planner_epoch,
)
from ark.agency.planner_journal_review import SyntheticPlanJournal


def _fixture(tmp_path):
    steps = (
        PlanStep("plan-a", ToolCall("fixture", "local.read", "offline", {})),
        PlanStep(
            "plan-b", ToolCall("fixture", "local.read", "offline", {}),
            ("plan-a",),
        ),
    )
    journal = SyntheticPlanJournal(tmp_path / "detached-digest.sqlite", steps)
    genesis = journal.recover().tail
    running = journal.append(
        "plan-a", StepState.RUNNING, expected_revision=0,
        at_ms=100, retained=genesis,
    )
    return journal, genesis, running


@pytest.mark.parametrize(
    ("statuses", "running"),
    (
        ((("plan-a", "running", 2), ("plan-b", "pending", 0)), ("plan-a",)),
        ((("plan-a", "succeeded", 1), ("plan-b", "pending", 0)), ()),
        ((("plan-a", "running", 1), ("plan-b", "cancelled", 1)), ("plan-a",)),
    ),
)
def test_valid_grammar_but_corrupted_status_digest_is_rejected(
    tmp_path, statuses, running,
):
    journal, genesis, recovered = _fixture(tmp_path)
    image = replace(
        recovered, step_statuses=statuses, ambiguous_running_steps=running,
    )
    with pytest.raises(PlannerEpochRecheckRejected, match="status digest"):
        recheck_disconnected_planner_epoch(journal, image, genesis)


@pytest.mark.parametrize(
    ("state", "revision"),
    (("pending", 1), ("running", 0), ("blocked", 0)),
)
def test_inconsistent_status_revision_is_not_benign_staleness(
    tmp_path, state, revision,
):
    journal, genesis, recovered = _fixture(tmp_path)
    altered = replace(
        recovered,
        step_statuses=(
            ("plan-a", state, revision), ("plan-b", "pending", 0),
        ),
        ambiguous_running_steps=("plan-a",) if state == "running" else (),
    )
    with pytest.raises(PlannerEpochRecheckRejected, match="status revision"):
        recheck_disconnected_planner_epoch(journal, altered, genesis)


def test_valid_older_image_is_drift_not_forgery(tmp_path):
    journal, genesis, running = _fixture(tmp_path)
    journal.append(
        "plan-a", StepState.SUCCEEDED, expected_revision=1,
        at_ms=200, retained=running.tail,
    )
    review = recheck_disconnected_planner_epoch(journal, running, genesis)
    assert review.local_freshness == "DRIFT_AT_READ"
    assert review.manual_review_required is True
    assert review.dispatch_authorized is False
    assert review.automatic_replay_authorized is False
