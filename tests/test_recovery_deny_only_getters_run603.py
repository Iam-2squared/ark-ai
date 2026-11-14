"""Detached WRITE crash diagnosis must never invoke counterfeit authority getters."""

from __future__ import annotations

import pytest

import ark.agency.synthetic_recovery_triage as mod
from ark.agency.audit import SQLiteActionAudit
from ark.agency.contracts import Effect, PlanStep, ToolCall
from ark.agency.durable_occurrence_review import SyntheticOccurrenceStore
from ark.agency.planner_journal_review import SyntheticPlanJournal
from ark.agency.registry import ToolRegistration, ToolRegistry


class NeverExecute:
    def execute(self, call):
        raise AssertionError("crash review must not dispatch a ToolBackend")


def _review(tmp_path):
    call = ToolCall("fixture", "fixture.write", "local", {"x": 1})
    journal = SyntheticPlanJournal(
        tmp_path / "planner.sqlite", (PlanStep("root", call),),
    )
    path = tmp_path / "reservations.sqlite"
    SyntheticOccurrenceStore(path)
    audit = SQLiteActionAudit(tmp_path / "audit.sqlite", clock_ms=lambda: 12)
    registry = ToolRegistry((
        ToolRegistration("fixture", "fixture.write", Effect.WRITE, "mock", NeverExecute()),
    ))
    return mod.review_synthetic_write_recovery(
        journal, path, audit, registry, call, step_id="root",
    )


@pytest.mark.parametrize("flag", (
    "dispatch_authorized",
    "automatic_replay_authorized",
    "external_outcome_known",
))
@pytest.mark.parametrize("when", ("preinstalled", "audit_callback"))
def test_forged_denial_descriptor_rejected_without_getter(
    tmp_path, monkeypatch, flag, when,
):
    getter_calls: list[int] = []

    class Counterfeit:
        def __get__(self, _instance, _owner=None):
            getter_calls.append(1)
            return False

    forged = Counterfeit()
    if when == "preinstalled":
        monkeypatch.setattr(mod.SyntheticRecoveryReview, flag, forged)
    else:
        original = mod.review_audit_continuity

        def inject(*args, **kwargs):
            review = original(*args, **kwargs)
            monkeypatch.setattr(mod.SyntheticRecoveryReview, flag, forged)
            return review

        monkeypatch.setattr(mod, "review_audit_continuity", inject)

    with pytest.raises(
        mod.SyntheticRecoveryRejected,
        match="constructed result changed authority",
    ):
        _review(tmp_path)
    assert getter_calls == []


def test_normal_pending_recovery_cannot_grant_action(tmp_path):
    result = _review(tmp_path)
    assert result.step_state == "pending"
    assert result.dispatch_authorized is False
    assert result.automatic_replay_authorized is False
    assert result.external_outcome_known is False
