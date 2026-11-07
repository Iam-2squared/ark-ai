"""Plan-wide recovery must not misclassify a WRITE via a replaced bind result.

Disposable SQLite stores and nonexecuting backends only; no live authorization.
"""

from dataclasses import replace

import pytest

from ark.agency.audit import SQLiteActionAudit
from ark.agency.contracts import Effect, PlanStep, ToolCall
from ark.agency.durable_occurrence_review import SyntheticOccurrenceStore
from ark.agency.planner_journal_review import SyntheticPlanJournal
from ark.agency.registry import ToolRegistration, ToolRegistry
from ark.agency.synthetic_write_plan_recovery_review import (
    SyntheticWritePlanReviewRejected,
    review_synthetic_write_plan,
)


class NeverExecute:
    def execute(self, _call):
        raise AssertionError("a disconnected recovery diagnostic executed a tool")


def _fixture(tmp_path):
    backend = NeverExecute()
    first = ToolCall("writer", "fixture.write", "local")
    second = ToolCall("writer", "fixture.write", "local", {"index": 2})
    reader = ToolCall("reader", "fixture.read", "local")
    registry = ToolRegistry((
        ToolRegistration("writer", "fixture.write", Effect.WRITE, "mock", backend),
        ToolRegistration("reader", "fixture.read", Effect.READ, "mock", backend),
    ))
    journal = SyntheticPlanJournal(tmp_path / "plan.sqlite", (
        PlanStep("one", first),
        PlanStep("two", second, ("one",)),
    ))
    ledger = tmp_path / "ledger.sqlite"
    SyntheticOccurrenceStore(ledger)
    audit = SQLiteActionAudit(tmp_path / "audit.sqlite", clock_ms=lambda: 10)
    return journal, ledger, audit, registry, first, second, reader


def _review(state):
    return review_synthetic_write_plan(*state[:4])


def test_unmodified_dependent_writes_remain_inert(tmp_path):
    review = _review(_fixture(tmp_path))
    assert tuple(step.step_id for step in review.steps) == ("one", "two")
    assert not review.dispatch_authorized
    assert not review.automatic_replay_authorized
    assert not review.external_outcome_known


def test_reentrant_read_binding_cannot_make_original_write_disappear(
    tmp_path, monkeypatch,
):
    state = _fixture(tmp_path)
    registry, original_call = state[3], state[4]
    original_bind = registry.bind

    def swapped(call):
        if call is not original_call:
            return original_bind(call)
        old_tool, old_capability = call.tool, call.capability
        object.__setattr__(call, "tool", "reader")
        object.__setattr__(call, "capability", "fixture.read")
        try:
            # A real, valid READ bind is returned for this temporarily altered
            # ToolCall, then the original WRITE fields are restored.
            return original_bind(call)
        finally:
            object.__setattr__(call, "tool", old_tool)
            object.__setattr__(call, "capability", old_capability)

    monkeypatch.setattr(registry, "bind", swapped)
    with pytest.raises(SyntheticWritePlanReviewRejected, match="binding changed"):
        _review(state)
    assert original_call.tool == "writer"


def test_binder_returning_another_call_is_not_accepted(tmp_path, monkeypatch):
    state = _fixture(tmp_path)
    registry, reader = state[3], state[6]
    original_bind = registry.bind

    def retargeted(_call):
        return original_bind(reader)

    monkeypatch.setattr(registry, "bind", retargeted)
    with pytest.raises(SyntheticWritePlanReviewRejected, match="binding changed"):
        _review(state)


@pytest.mark.parametrize("field", ("revision", "registration"))
def test_forged_bound_registration_or_revision_fails_closed(
    tmp_path, monkeypatch, field,
):
    state = _fixture(tmp_path)
    registry = state[3]
    original_bind = registry.bind

    def forged(call):
        bound = original_bind(call)
        if field == "revision":
            return replace(bound, registry_revision="tools_" + "0" * 64)
        return replace(bound, registration=registry.get("reader"))

    monkeypatch.setattr(registry, "bind", forged)
    with pytest.raises(SyntheticWritePlanReviewRejected, match="binding changed"):
        _review(state)
