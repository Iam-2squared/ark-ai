"""Synthetic Planner ambiguity budget before any follow-up journal read.

RUNNING-after-crash remains UNKNOWN, manual-only and never a replay grant.
"""

from dataclasses import replace

import pytest

from ark.agency.contracts import PlanStep, StepState, ToolCall
from ark.agency.disconnected_planner_epoch_recheck import (
    PlannerEpochRecheckRejected,
    recheck_disconnected_planner_epoch,
)
from ark.agency.planner_journal_review import SyntheticPlanJournal


@pytest.mark.parametrize("count", (2, 25, 10_000))
def test_oversized_running_inventory_is_rejected_before_journal_recovery(
    tmp_path, monkeypatch: pytest.MonkeyPatch, count: int,
) -> None:
    journal = SyntheticPlanJournal(
        tmp_path / "disconnected-planner.sqlite",
        (PlanStep("root", ToolCall("reader", "fixture.read", "local", {"v": 1})),),
    )
    genesis = journal.recover().tail
    running = journal.append(
        "root", StepState.RUNNING, expected_revision=0,
        at_ms=10, retained=genesis,
    )
    forged = replace(
        running, ambiguous_running_steps=("root",) * count,
    )
    visited = []

    def forbidden_path():
        visited.append("journal filesystem access")
        raise AssertionError("invalid detached Planner image reached SQLite")

    monkeypatch.setattr(journal, "_assert_source_path", forbidden_path)
    with pytest.raises(PlannerEpochRecheckRejected, match="Planner image malformed"):
        recheck_disconnected_planner_epoch(journal, forged, genesis)
    assert visited == []
