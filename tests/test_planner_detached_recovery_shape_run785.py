"""Detached Planner images must pass exact status grammar before journal replay.

Only disposable, synthetic SQLite plan state is involved; no ToolBackend is
created, and MATCH_AT_READ never authorizes dispatch or automatic replay.
"""

from dataclasses import replace

import pytest

from ark.agency.contracts import PlanStep, StepState, ToolCall
from ark.agency.disconnected_planner_epoch_recheck import (
    PlannerEpochRecheckRejected,
    recheck_disconnected_planner_epoch,
)
from ark.agency.planner_journal_review import SyntheticPlanJournal

_A = "planner-a"
_B = "planner-b"


def _fixture(tmp_path):
    steps = (
        PlanStep(_A, ToolCall("fixture", "local.read", "offline", {})),
        PlanStep(_B, ToolCall("fixture", "local.read", "offline", {}), (_A,)),
    )
    journal = SyntheticPlanJournal(tmp_path / "local-plan.sqlite", steps)
    genesis = journal.recover().tail
    recovered = journal.append(
        _A, StepState.RUNNING, expected_revision=0,
        at_ms=100, retained=genesis,
    )
    return journal, genesis, recovered


@pytest.mark.parametrize(
    ("statuses", "running"),
    (
        (((_A, "unexpected", 1), (_B, "pending", 0)), (_A,)),
        (((_A, "running", True), (_B, "pending", 0)), (_A,)),
        (((_A, "running", -1), (_B, "pending", 0)), (_A,)),
        (((_A, "running", 2**63), (_B, "pending", 0)), (_A,)),
        (((_A, "running", 1), (_A, "pending", 0)), (_A,)),
        (((_B, "pending", 0), (_A, "running", 1)), (_A,)),
        (((_A, "running", 1), (_B, "pending", 0)), (_B,)),
        (((_A, "running", 1), (_B, "pending", 0)), (_A, _A)),
        (((" ", "running", 1), (_B, "pending", 0)), (" ",)),
    ),
)
def test_invalid_detached_planner_status_image_is_not_staleness(
    tmp_path, statuses, running,
):
    journal, genesis, recovered = _fixture(tmp_path)
    altered = replace(
        recovered, step_statuses=statuses, ambiguous_running_steps=running,
    )
    with pytest.raises(PlannerEpochRecheckRejected, match="malformed"):
        recheck_disconnected_planner_epoch(journal, altered, genesis)


def test_genuine_running_snapshot_remains_manual_only(tmp_path):
    journal, genesis, recovered = _fixture(tmp_path)
    review = recheck_disconnected_planner_epoch(journal, recovered, genesis)
    assert review.local_freshness == "MATCH_AT_READ"
    assert review.manual_review_required is True
    assert review.dispatch_authorized is False
    assert review.automatic_replay_authorized is False
