"""A detached Planner projection must bind statuses to its replay tail.

These are local, disconnected SQLite fixture observations. Neither a matched
digest nor READY_MOCK_ONLY authenticates an actor or permits tool execution.
"""

from __future__ import annotations

from dataclasses import replace

import pytest

from ark.agency.contracts import PlanStep, StepState, ToolCall
from ark.agency.disconnected_planner_fence_projection import (
    DisconnectedPlannerProjectionRejected,
    project_disconnected_planner_fence,
)
from ark.agency.planner_journal_review import SyntheticPlanJournal

ROOT = "step_" + "1" * 16


def _setup(tmp_path):
    step = PlanStep(
        ROOT, ToolCall("local-fixture", "read", "private", {"fixture": 1}),
    )
    steps = (step,)
    journal = SyntheticPlanJournal(tmp_path / "project-digest.sqlite", steps)
    return journal, steps


@pytest.mark.parametrize(
    ("state", "revision", "running"),
    (
        ("pending", 1, ()),
        ("failed", 0, ()),
        ("running", 0, (ROOT,)),
    ),
)
def test_forged_status_or_revision_must_not_reuse_retained_tail(
    tmp_path, state, revision, running,
):
    journal, steps = _setup(tmp_path)
    genuine = journal.recover()
    forged = replace(
        genuine,
        step_statuses=((ROOT, state, revision),),
        ambiguous_running_steps=running,
    )
    assert forged.tail is genuine.tail
    with pytest.raises(
        DisconnectedPlannerProjectionRejected,
        match="statuses differ from retained tail",
    ):
        project_disconnected_planner_fence(
            forged, steps, ((ROOT, "READ"),),
        )
    # No SQLite append is permitted as a side effect of a projection.
    assert journal.recover() == genuine


def test_real_terminal_journal_snapshot_is_consistent_but_never_authorizes(tmp_path):
    journal, steps = _setup(tmp_path)
    baseline = journal.recover()
    journal.append(
        ROOT, StepState.RUNNING,
        expected_revision=0, at_ms=100, retained=baseline.tail,
    )
    journal.append(
        ROOT, StepState.FAILED,
        expected_revision=1, at_ms=101, retained=baseline.tail,
    )
    restored = SyntheticPlanJournal(journal._path, steps).recover(
        retained=baseline.tail,
    )
    view = project_disconnected_planner_fence(
        restored, steps, ((ROOT, "READ"),),
    )
    assert tuple((step.step_id, step.code) for step in view.decisions) == (
        (ROOT, "TERMINAL"),
    )
    assert view.dispatch_authorized is False
    assert view.automatic_replay_authorized is False
    assert view.write_authorized is False
    assert view.external_outcome_verified is False
