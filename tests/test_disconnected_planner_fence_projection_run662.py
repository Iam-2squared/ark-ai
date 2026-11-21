"""Synthetic Planner restart projects to an inert mock-only hold view.

The adapter uses explicit untrusted READ/WRITE labels, never ToolRegistry
approval, backend execution or an invented SUCCEEDED result receipt.
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

ROOT = "step_" + "a" * 16
CHILD = "step_" + "b" * 16
JOIN = "step_" + "c" * 16
READ = "step_" + "d" * 16
WRITE = "step_" + "e" * 16


def _steps():
    def step(name, *deps):
        return PlanStep(
            name,
            ToolCall("fixture", "offline", "local", {"step": name}),
            deps,
        )

    # The input order is deliberately not dependency-first.
    return (
        step(JOIN, CHILD, READ),
        step(WRITE),
        step(READ),
        step(CHILD, ROOT),
        step(ROOT),
    )


def _effects():
    return (
        (ROOT, "READ"),
        (CHILD, "WRITE"),
        (JOIN, "READ"),
        (READ, "READ"),
        (WRITE, "WRITE"),
    )


def _journal(tmp_path):
    steps = _steps()
    journal = SyntheticPlanJournal(tmp_path / "projection.sqlite", steps)
    return journal, steps


def _codes(view):
    assert view.dispatch_authorized is False
    assert view.automatic_replay_authorized is False
    assert view.write_authorized is False
    assert view.external_outcome_verified is False
    return {decision.step_id: decision.code for decision in view.decisions}


def test_restarted_running_read_quarantines_descendant_write_and_join(tmp_path):
    journal, steps = _journal(tmp_path)
    initial = journal.recover().tail
    journal.append(ROOT, StepState.RUNNING, expected_revision=0,
                   at_ms=10, retained=initial)
    recovered = SyntheticPlanJournal(journal._path, steps).recover(retained=initial)
    assert recovered.ambiguous_running_steps == (ROOT,)
    before = recovered
    view = project_disconnected_planner_fence(recovered, steps, _effects())
    assert _codes(view) == {
        ROOT: "QUARANTINE_UNKNOWN",
        CHILD: "HOLD_UNCERTAIN",
        JOIN: "HOLD_UNCERTAIN",
        READ: "READY_MOCK_ONLY",
        WRITE: "HELD_WRITE_APPROVAL",
    }
    assert view == project_disconnected_planner_fence(recovered, steps, _effects())
    assert journal.recover(retained=initial) == before


@pytest.mark.parametrize("terminal", (StepState.FAILED, StepState.CANCELLED))
def test_terminal_root_remains_blocked_in_detached_projection(tmp_path, terminal):
    journal, steps = _journal(tmp_path)
    initial = journal.recover().tail
    journal.append(ROOT, StepState.RUNNING, expected_revision=0,
                   at_ms=10, retained=initial)
    journal.append(ROOT, terminal, expected_revision=1,
                   at_ms=11, retained=initial)
    recovered = SyntheticPlanJournal(journal._path, steps).recover(retained=initial)
    view = project_disconnected_planner_fence(recovered, steps, _effects())
    assert _codes(view) == {
        ROOT: "TERMINAL",
        CHILD: "TERMINAL",
        JOIN: "TERMINAL",
        READ: "READY_MOCK_ONLY",
        WRITE: "HELD_WRITE_APPROVAL",
    }


def test_succeeded_step_cannot_fabricate_missing_result_receipt(tmp_path):
    journal, steps = _journal(tmp_path)
    initial = journal.recover().tail
    journal.append(ROOT, StepState.RUNNING, expected_revision=0,
                   at_ms=10, retained=initial)
    journal.append(ROOT, StepState.SUCCEEDED, expected_revision=1,
                   at_ms=11, retained=initial)
    recovered = journal.recover(retained=initial)
    with pytest.raises(
        DisconnectedPlannerProjectionRejected, match="unsupported, unverified",
    ):
        project_disconnected_planner_fence(recovered, steps, _effects())


@pytest.mark.parametrize(
    "effects",
    (
        ((ROOT, "READ"),),
        ((ROOT, "READ"), (ROOT, "WRITE"), (JOIN, "READ"), (READ, "READ"), (WRITE, "WRITE")),
        ((ROOT, "DELETE"), (CHILD, "WRITE"), (JOIN, "READ"), (READ, "READ"), (WRITE, "WRITE")),
    ),
)
def test_incomplete_duplicate_or_nonexact_effects_fail_closed(tmp_path, effects):
    journal, steps = _journal(tmp_path)
    with pytest.raises(DisconnectedPlannerProjectionRejected):
        project_disconnected_planner_fence(journal.recover(), steps, effects)


def test_unrelated_topology_never_reuses_a_retained_plan_status(tmp_path):
    journal, steps = _journal(tmp_path)
    recovered = journal.recover()
    different = tuple(
        replace(step, call=ToolCall("fixture", "offline", "local", {"different": 1}))
        if step.step_id == ROOT else step
        for step in steps
    )
    with pytest.raises(
        DisconnectedPlannerProjectionRejected, match="topology differs",
    ):
        project_disconnected_planner_fence(recovered, different, _effects())


def test_mutated_running_membership_does_not_become_ready(tmp_path):
    journal, steps = _journal(tmp_path)
    recovered = journal.recover()
    changed = replace(recovered, ambiguous_running_steps=(ROOT,))
    with pytest.raises(
        DisconnectedPlannerProjectionRejected, match="membership",
    ):
        project_disconnected_planner_fence(changed, steps, _effects())
