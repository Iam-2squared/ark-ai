"""Reentrant valid Planner transitions must not publish stale status witnesses.

These are disconnected synthetic plans. No backend, consent, external effect,
or durable journal is involved.
"""

import pytest

import ark.agency.planner as planner_module
from ark.agency import PlanConflictError, PlanGraph, PlanStep, StepState, ToolCall


def _graph() -> PlanGraph:
    return PlanGraph((
        PlanStep("read", ToolCall("fixture.read", "offline", "local")),
        PlanStep(
            "dependent",
            ToolCall("fixture.write", "offline", "local"),
            ("read",),
        ),
    ))


def test_valid_transition_during_digest_callback_rejects_stale_witness(monkeypatch):
    graph = _graph()
    original = planner_module._plan_digest
    called = []

    def digest(prefix, payload):
        if prefix == "pstate_":
            called.append(prefix)
            graph.transition("read", StepState.RUNNING, expected_revision=0)
        return original(prefix, payload)

    with monkeypatch.context() as changes:
        changes.setattr(planner_module, "_plan_digest", digest)
        with pytest.raises(PlanConflictError, match="status changed during digest"):
            graph.status_digest()

    assert called == ["pstate_"]
    assert graph.statuses()["read"].state is StepState.RUNNING
    assert graph.statuses()["read"].revision == 1


def test_valid_transition_during_detached_copy_rejects_stale_snapshot(monkeypatch):
    graph = _graph()
    initial = graph._status["read"]
    original = planner_module.replace
    called = []

    def reentrant_copy(value, **changes):
        if value is initial and not changes and not called:
            called.append("copy")
            graph.transition("read", StepState.RUNNING, expected_revision=0)
        return original(value, **changes)

    with monkeypatch.context() as patches:
        patches.setattr(planner_module, "replace", reentrant_copy)
        with pytest.raises(PlanConflictError, match="status changed during detached snapshot"):
            graph.statuses()

    assert called == ["copy"]
    assert graph.statuses()["read"].state is StepState.RUNNING


def test_uninterrupted_status_witness_still_deterministic():
    graph = _graph()
    original = graph.status_digest()
    assert graph.status_digest() == original
    assert graph.statuses()["read"].state is StepState.PENDING

    graph.transition("read", StepState.RUNNING, expected_revision=0)
    newer = graph.status_digest()
    assert newer != original
    assert graph.status_digest() == newer
    assert graph.statuses()["dependent"].state is StepState.PENDING
