"""Synthetic journal recovery respects the 24-step detached fence budget.

READ readiness is only a mock preview; no tool or authorization is consulted.
"""
from __future__ import annotations

import pytest

from ark.agency.contracts import PlanStep, ToolCall
from ark.agency.disconnected_planner_fence_projection import (
    DisconnectedPlannerProjectionRejected,
    project_disconnected_planner_fence,
)
from ark.agency.planner_journal_review import SyntheticPlanJournal


def _chain(n):
    steps = []
    for i in range(n):
        name = f"step_{i:016x}"
        deps = (f"step_{i - 1:016x}",) if i else ()
        steps.append(
            PlanStep(name, ToolCall("fixture", "offline", "local", {"index": i}), deps)
        )
    return tuple(reversed(steps))


@pytest.mark.parametrize("count", (1, 24))
@pytest.mark.parametrize("root_effect", ("READ", "WRITE"))
def test_maximum_bounded_restart_chain_is_inert_and_dependency_ordered(
    tmp_path, count, root_effect,
):
    steps = _chain(count)
    journal = SyntheticPlanJournal(tmp_path / "chain.sqlite", steps)
    recovered = journal.recover()
    effects = tuple(
        (step.step_id, root_effect if step.step_id == "step_0000000000000000"
         else "READ")
        for step in steps
    )

    report = project_disconnected_planner_fence(recovered, steps, effects)
    ordered = [d.step_id for d in report.decisions]
    assert ordered == [f"step_{i:016x}" for i in range(count)]
    assert report.decisions[0].code == (
        "READY_MOCK_ONLY" if root_effect == "READ" else "HELD_WRITE_APPROVAL"
    )
    assert all(d.code == "WAIT_DEPENDENCY" for d in report.decisions[1:])
    assert report.dispatch_authorized is False
    assert report.write_authorized is False
    assert report.automatic_replay_authorized is False
    assert report.external_outcome_verified is False
    assert project_disconnected_planner_fence(recovered, steps, effects) == report
    assert journal.recover() == recovered


def test_25th_step_is_rejected_before_building_a_recovery_fence(tmp_path):
    steps = _chain(24)
    journal = SyntheticPlanJournal(tmp_path / "limit.sqlite", steps)
    recovered = journal.recover()
    extra = _chain(25)
    labels = tuple((step.step_id, "READ") for step in extra)
    with pytest.raises(
        DisconnectedPlannerProjectionRejected, match="exact detached projection inputs",
    ):
        project_disconnected_planner_fence(recovered, extra, labels)
    assert journal.recover() == recovered


@pytest.mark.parametrize("bad_effects", ("alias", "duplicate"))
def test_effect_claim_identity_cannot_bypass_topology(tmp_path, bad_effects):
    steps = _chain(2)
    journal = SyntheticPlanJournal(tmp_path / "effects.sqlite", steps)
    recovered = journal.recover()

    class EffectAlias(str):
        pass

    if bad_effects == "alias":
        effects = (
            (steps[0].step_id, EffectAlias("READ")),
            (steps[1].step_id, "READ"),
        )
    else:
        effects = (
            (steps[0].step_id, "READ"),
            (steps[0].step_id, "READ"),
        )
    with pytest.raises(DisconnectedPlannerProjectionRejected):
        project_disconnected_planner_fence(recovered, steps, effects)
    assert journal.recover() == recovered
