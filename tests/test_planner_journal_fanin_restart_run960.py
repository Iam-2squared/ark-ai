"""Persisted terminal fan-in must remain blocked across cold journal handles.

These are local synthetic Planner fixtures; no ToolBackend is dispatched and a
retained SQLite prefix never becomes execution or consent authority.
"""

from __future__ import annotations

import sqlite3

import pytest

from ark.agency.contracts import PlanConflictError, PlanStep, StepState, ToolCall
from ark.agency.planner_journal_review import SyntheticPlanJournal


def _steps() -> tuple[PlanStep, ...]:
    call = ToolCall("synthetic.read", "fixture.read", "private")
    return (
        PlanStep("root-a", call),
        PlanStep("root-b", call),
        PlanStep("join", call, ("root-a", "root-b")),
        PlanStep("leaf", call, ("join",)),
        PlanStep("unrelated", call),
    )


@pytest.mark.parametrize("terminal", (StepState.FAILED, StepState.CANCELLED))
@pytest.mark.parametrize("sibling_first", (False, True))
def test_terminal_join_cannot_reopen_after_cold_recovery(
    tmp_path, terminal: StepState, sibling_first: bool,
) -> None:
    path = tmp_path / "terminal-fanin.sqlite"
    steps = _steps()
    journal = SyntheticPlanJournal(path, steps)
    original = journal.recover().tail
    at_ms = 100

    def apply(step: str, state: StepState, revision: int) -> None:
        nonlocal at_ms
        # A separate journal handle for every operation verifies cold replay
        # rather than trusting a single cached in-memory PlanGraph.
        SyntheticPlanJournal(path, steps).append(
            step, state, expected_revision=revision,
            at_ms=at_ms, retained=original,
        )
        at_ms += 1

    if sibling_first:
        apply("root-b", StepState.RUNNING, 0)
        apply("root-b", StepState.SUCCEEDED, 1)
    apply("root-a", StepState.RUNNING, 0)
    apply("root-a", terminal, 1)
    if not sibling_first:
        apply("root-b", StepState.RUNNING, 0)
        apply("root-b", StepState.SUCCEEDED, 1)

    cold = SyntheticPlanJournal(path, steps)
    result = cold.recover(retained=original)
    statuses = {key: (state, revision) for key, state, revision in result.step_statuses}
    assert statuses["root-a"] == (terminal.value, 2)
    assert statuses["root-b"] == ("succeeded", 2)
    assert statuses["join"] == ("blocked", 1)
    assert statuses["leaf"] == ("blocked", 1)
    assert statuses["unrelated"] == ("pending", 0)
    assert result.tail.event_count == 4
    assert result.ambiguous_running_steps == ()
    assert result.dispatch_authorized is False
    assert result.automatic_replay_authorized is False

    for blocked in ("join", "leaf"):
        with pytest.raises(PlanConflictError):
            SyntheticPlanJournal(path, steps).append(
                blocked, StepState.RUNNING, expected_revision=1,
                at_ms=at_ms, retained=original,
            )
    assert cold.recover().tail == result.tail

    # A separate, unrelated step remains independently runnable.
    apply("unrelated", StepState.RUNNING, 0)
    apply("unrelated", StepState.SUCCEEDED, 1)
    after = SyntheticPlanJournal(path, steps).recover(retained=original)
    final = {key: (state, rev) for key, state, rev in after.step_statuses}
    assert final["unrelated"] == ("succeeded", 2)
    assert final["join"] == ("blocked", 1)
    assert final["leaf"] == ("blocked", 1)
    assert after.tail.event_count == 6
    assert after.dispatch_authorized is False
    assert after.automatic_replay_authorized is False

    with sqlite3.connect(path) as conn:
        assert conn.execute("PRAGMA quick_check").fetchone() == ("ok",)
        assert conn.execute(
            "SELECT COUNT(*) FROM synthetic_plan_events"
        ).fetchone() == (6,)
        assert conn.execute(
            "SELECT event_count FROM synthetic_plan_header WHERE id=1"
        ).fetchone() == (6,)
