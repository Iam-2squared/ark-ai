"""Offline Planner recovery may not silently adopt a retargeted ToolCall.

Only synthetic journal transitions and detached hold views are exercised.
A READY_MOCK_ONLY classification is never a dispatch grant or real receipt.
"""

from __future__ import annotations

import sqlite3
from types import MappingProxyType

import pytest

from ark.agency import disconnected_planner_fence_projection as projection
from ark.agency.contracts import PlanStep, StepState, ToolCall
from ark.agency.planner_journal_review import SyntheticPlanJournal

_ROOT = "step_" + "1" * 16
_CHILD = "step_" + "2" * 16


def _fixture(tmp_path):
    steps = (
        PlanStep(_ROOT, ToolCall("fixture", "read", "local:private", {"a": 1})),
        PlanStep(
            _CHILD, ToolCall("fixture", "write", "local:private", {"b": 2}),
            (_ROOT,),
        ),
    )
    effects = ((_ROOT, "READ"), (_CHILD, "WRITE"))
    journal = SyntheticPlanJournal(tmp_path / "plan-identity.sqlite", steps)
    return journal, steps, effects


@pytest.mark.parametrize("retarget", ("tool", "scope", "equal-arguments"))
def test_digest_callback_cannot_retarget_nested_call_without_rejection(
    tmp_path, monkeypatch, retarget,
):
    journal, steps, effects = _fixture(tmp_path)
    before = journal.recover()
    original_digest = projection._plan_digest
    called = []

    def adversarial_digest(prefix, payload):
        called.append(retarget)
        call = steps[0].call
        if retarget == "tool":
            object.__setattr__(call, "tool", "retargeted-fixture")
        elif retarget == "scope":
            object.__setattr__(call, "scope", "local:another")
        else:
            # Same canonical JSON / same request ID, different object identity.
            replacement = MappingProxyType(dict(call.arguments))
            assert replacement == call.arguments
            assert replacement is not call.arguments
            object.__setattr__(call, "arguments", replacement)
        return original_digest(prefix, payload)

    monkeypatch.setattr(projection, "_plan_digest", adversarial_digest)
    with pytest.raises(
        projection.DisconnectedPlannerProjectionRejected,
        match="projection inputs changed",
    ):
        projection.project_disconnected_planner_fence(before, steps, effects)
    assert called == [retarget]
    with sqlite3.connect(journal._path) as conn:
        assert conn.execute("SELECT event_count FROM synthetic_plan_header").fetchone() == (0,)
        assert conn.execute("SELECT COUNT(*) FROM synthetic_plan_events").fetchone() == (0,)


def test_recovered_success_without_result_receipt_is_rejected_not_invented(tmp_path):
    journal, steps, effects = _fixture(tmp_path)
    initial = journal.recover()
    journal.append(
        _ROOT, StepState.RUNNING, expected_revision=0,
        at_ms=100, retained=initial.tail,
    )
    journal.append(
        _ROOT, StepState.SUCCEEDED, expected_revision=1,
        at_ms=101, retained=initial.tail,
    )
    restarted = SyntheticPlanJournal(journal._path, steps).recover(
        retained=initial.tail,
    )
    assert (_ROOT, "succeeded", 2) in restarted.step_statuses
    before_events = restarted.tail.event_count
    with pytest.raises(
        projection.DisconnectedPlannerProjectionRejected,
        match="unverified",
    ):
        projection.project_disconnected_planner_fence(restarted, steps, effects)
    assert journal.recover().tail.event_count == before_events


def test_forged_revision_cannot_create_detached_ready_state(tmp_path):
    journal, steps, effects = _fixture(tmp_path)
    restarted = journal.recover()
    forged_status = tuple(
        (step, state, revision + 1 if step == _ROOT else revision)
        for step, state, revision in restarted.step_statuses
    )
    object.__setattr__(restarted, "step_statuses", forged_status)
    with pytest.raises(
        projection.DisconnectedPlannerProjectionRejected,
        match="digest",
    ):
        projection.project_disconnected_planner_fence(restarted, steps, effects)
    with sqlite3.connect(journal._path) as conn:
        assert conn.execute("SELECT COUNT(*) FROM synthetic_plan_events").fetchone() == (0,)
