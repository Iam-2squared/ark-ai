"""Disconnected multi-step Planner recovery preserves dependency holds.

All plans, effects and clocks here are synthetic SQLite fixtures. The only
READY label is mock-only; no tool, permission or backend can be invoked.
"""

from __future__ import annotations

import pytest

from ark.agency.contracts import PlanStep, StepState, ToolCall
from ark.agency.disconnected_planner_fence_projection import (
    DisconnectedPlannerProjectionRejected,
    project_disconnected_planner_fence,
)
from ark.agency.planner_journal_review import SyntheticPlanJournal

ROOT, WRITE, CHILD_READ, INDEPENDENT = (
    "step_" + digit * 16 for digit in "1234"
)


def _fixture(tmp_path):
    steps = (
        PlanStep(ROOT, ToolCall("local", "read", "private", {"case": 1})),
        PlanStep(
            WRITE, ToolCall("local", "write", "private", {"case": 2}), (ROOT,),
        ),
        PlanStep(
            CHILD_READ, ToolCall("local", "read", "private", {"case": 3}), (ROOT,),
        ),
        PlanStep(
            INDEPENDENT, ToolCall("local", "read", "private", {"case": 4}),
        ),
    )
    effects = (
        (ROOT, "READ"), (WRITE, "WRITE"),
        (CHILD_READ, "READ"), (INDEPENDENT, "READ"),
    )
    journal = SyntheticPlanJournal(tmp_path / "projection-dag.sqlite", steps)
    return journal, steps, effects


def _codes(view):
    assert view.dispatch_authorized is False
    assert view.automatic_replay_authorized is False
    assert view.write_authorized is False
    assert view.external_outcome_verified is False
    return {decision.step_id: decision.code for decision in view.decisions}


def test_unstarted_dependency_dag_is_not_a_permission_to_run(tmp_path):
    journal, steps, effects = _fixture(tmp_path)
    recovery = journal.recover()
    codes = _codes(project_disconnected_planner_fence(recovery, steps, effects))
    assert codes == {
        ROOT: "READY_MOCK_ONLY",
        WRITE: "WAIT_DEPENDENCY",
        CHILD_READ: "WAIT_DEPENDENCY",
        INDEPENDENT: "READY_MOCK_ONLY",
    }
    assert journal.recover() == recovery


def test_restarted_running_read_quarantines_only_dependent_subgraph(tmp_path):
    journal, steps, effects = _fixture(tmp_path)
    baseline = journal.recover()
    journal.append(
        ROOT, StepState.RUNNING,
        expected_revision=0, at_ms=100, retained=baseline.tail,
    )
    restored = SyntheticPlanJournal(journal._path, steps).recover(
        retained=baseline.tail,
    )
    codes = _codes(project_disconnected_planner_fence(restored, steps, effects))
    assert codes == {
        ROOT: "QUARANTINE_UNKNOWN",
        WRITE: "HOLD_UNCERTAIN",
        CHILD_READ: "HOLD_UNCERTAIN",
        INDEPENDENT: "READY_MOCK_ONLY",
    }


def test_terminal_failure_blocks_children_not_independent_read(tmp_path):
    journal, steps, effects = _fixture(tmp_path)
    initial = journal.recover()
    journal.append(
        ROOT, StepState.RUNNING,
        expected_revision=0, at_ms=100, retained=initial.tail,
    )
    journal.append(
        ROOT, StepState.FAILED,
        expected_revision=1, at_ms=101, retained=initial.tail,
    )
    restored = SyntheticPlanJournal(journal._path, steps).recover(
        retained=initial.tail,
    )
    codes = _codes(project_disconnected_planner_fence(restored, steps, effects))
    assert codes == {
        ROOT: "TERMINAL",
        WRITE: "TERMINAL",
        CHILD_READ: "TERMINAL",
        INDEPENDENT: "READY_MOCK_ONLY",
    }


@pytest.mark.parametrize(
    "forged_effects",
    (
        ((ROOT, "READ"), (WRITE, "READ"), (CHILD_READ, "READ"), (ROOT, "READ")),
        ((ROOT, "READ"), (WRITE, "WRITE"), (CHILD_READ, "READ"), ("other", "READ")),
        ((ROOT, "READ"), (WRITE, "write"), (CHILD_READ, "READ"), (INDEPENDENT, "READ")),
    ),
)
def test_wrong_effect_membership_or_case_fails_without_journal_write(
    tmp_path, forged_effects,
):
    journal, steps, _effects = _fixture(tmp_path)
    before = journal.recover()
    with pytest.raises(DisconnectedPlannerProjectionRejected):
        project_disconnected_planner_fence(before, steps, forged_effects)
    assert journal.recover() == before
