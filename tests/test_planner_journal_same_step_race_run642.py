"""Two distinct journal handles cannot both claim one RUNNING transition.

This is a disconnected, temporary SQLite concurrency fixture. A lost CAS or
a nonmonotonic timestamp must never produce a second durable transition,
and recovered RUNNING is not a new dispatch/replay authorization.
"""

from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
from threading import Barrier

import pytest

from ark.agency.contracts import PlanConflictError, PlanStep, StepState, ToolCall
from ark.agency.planner_journal_review import (
    SyntheticPlanJournal,
    SyntheticPlanJournalRejected,
)


@pytest.mark.parametrize("owner", ("en", "日本語"))
def test_competing_same_root_start_has_only_one_durable_winner(tmp_path, owner):
    path = tmp_path / "concurrent-same-root.sqlite"
    call = ToolCall("fixture", "offline", owner, {"fixture": True})
    steps = (PlanStep("root", call),)
    first = SyntheticPlanJournal(path, steps)
    second = SyntheticPlanJournal(path, steps)
    prior = first.recover().tail
    barrier = Barrier(2)

    def attempt(journal):
        barrier.wait(timeout=10)
        try:
            result = journal.append(
                "root", StepState.RUNNING, expected_revision=0,
                at_ms=100, retained=prior,
            )
        except PlanConflictError:
            return ("stale", None)
        return ("started", result)

    with ThreadPoolExecutor(max_workers=2) as workers:
        results = list(workers.map(attempt, (first, second)))
    assert sorted(name for name, _ in results) == ["stale", "started"]

    restart = SyntheticPlanJournal(path, steps).recover(retained=prior)
    assert restart.tail.event_count == 1
    assert restart.step_statuses == (("root", "running", 1),)
    assert restart.ambiguous_running_steps == ("root",)
    assert restart.dispatch_authorized is False
    assert restart.automatic_replay_authorized is False


def test_regressed_journal_clock_and_stale_revision_cannot_append(tmp_path):
    path = tmp_path / "clock-bound-plan.sqlite"
    steps = (PlanStep(
        "root", ToolCall("fixture", "offline", "local", {"dry_run": True}),
    ),)
    journal = SyntheticPlanJournal(path, steps)
    prior = journal.recover().tail
    running = journal.append(
        "root", StepState.RUNNING, expected_revision=0,
        at_ms=200, retained=prior,
    )

    with pytest.raises(
        SyntheticPlanJournalRejected, match="capacity or clock regression",
    ):
        journal.append(
            "root", StepState.SUCCEEDED, expected_revision=1,
            at_ms=199, retained=running.tail,
        )
    assert SyntheticPlanJournal(path, steps).recover() == running

    with pytest.raises(PlanConflictError):
        journal.append(
            "root", StepState.RUNNING, expected_revision=0,
            at_ms=201, retained=running.tail,
        )
    recovered = SyntheticPlanJournal(path, steps).recover(retained=prior)
    assert recovered == running
    assert recovered.ambiguous_running_steps == ("root",)
    assert recovered.automatic_replay_authorized is False
