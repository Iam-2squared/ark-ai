"""The detached Planner projection cannot substitute a fence reviewer.

All examples use a local, never-dispatched journal. A READY_MOCK_ONLY label
is a diagnostic, not an authorization or a verified external result.
"""

from __future__ import annotations

import pytest

from ark.agency import disconnected_planner_fence_projection as projection
from ark.agency import disconnected_write_recovery_fence as fence_module
from ark.agency.contracts import PlanStep, ToolCall
from ark.agency.planner_journal_review import SyntheticPlanJournal

_ROOT = "step_" + "1" * 16
_CHILD = "step_" + "2" * 16


def _fixture(tmp_path):
    steps = (
        PlanStep(_ROOT, ToolCall("fixture", "read", "local:private", {"x": 1})),
        PlanStep(
            _CHILD, ToolCall("fixture", "write", "local:private", {"x": 2}),
            (_ROOT,),
        ),
    )
    effects = ((_ROOT, "READ"), (_CHILD, "WRITE"))
    journal = SyntheticPlanJournal(tmp_path / "inert-projection.sqlite", steps)
    return journal, journal.recover(), steps, effects


def test_original_review_gives_deterministic_inert_plan_without_append(tmp_path):
    journal, recovered, steps, effects = _fixture(tmp_path)
    view = projection.project_disconnected_planner_fence(recovered, steps, effects)
    assert view.plan_id == recovered.tail.topology_digest
    assert {item.step_id: item.code for item in view.decisions} == {
        _ROOT: "READY_MOCK_ONLY",
        _CHILD: "WAIT_DEPENDENCY",
    }
    assert view.dispatch_authorized is False
    assert view.automatic_replay_authorized is False
    assert view.write_authorized is False
    assert view.external_outcome_verified is False
    assert journal.recover().tail.event_count == 0


@pytest.mark.parametrize("target", ("projection", "source"))
def test_replaced_review_callback_is_never_executed(
    tmp_path, monkeypatch, target,
):
    journal, recovered, steps, effects = _fixture(tmp_path)
    calls = []

    def forged_review(*args):
        calls.append(args)
        raise AssertionError("unsafe injected callback executed")

    module = projection if target == "projection" else fence_module
    monkeypatch.setattr(module, "review_disconnected_recovery_fence", forged_review)
    with pytest.raises(
        projection.DisconnectedPlannerProjectionRejected,
        match="review authority changed",
    ):
        projection.project_disconnected_planner_fence(recovered, steps, effects)
    assert calls == []
    assert journal.recover().tail.event_count == 0


@pytest.mark.parametrize(
    "carrier, attribute",
    (
        ("fence", "dispatch_authorized"),
        ("claim", "__init__"),
    ),
)
def test_replaced_carrier_code_is_refused_before_execution(
    tmp_path, monkeypatch, carrier, attribute,
):
    journal, recovered, steps, effects = _fixture(tmp_path)
    calls = []

    if carrier == "fence":
        def unsafe_getter(self):
            calls.append(self)
            raise AssertionError("unsafe injected getter executed")

        monkeypatch.setattr(
            fence_module.OfflineRecoveryFence, attribute,
            property(unsafe_getter),
        )
    else:
        def unsafe_init(self, *args):
            calls.append(args)
            raise AssertionError("unsafe injected initializer executed")

        monkeypatch.setattr(
            fence_module.OfflineRecoveryStepClaim, attribute, unsafe_init,
        )

    with pytest.raises(
        projection.DisconnectedPlannerProjectionRejected,
        match="carrier authority changed",
    ):
        projection.project_disconnected_planner_fence(recovered, steps, effects)
    assert calls == []
    assert journal.recover().tail.event_count == 0
