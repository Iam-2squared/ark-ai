"""Constructed plan-wide recovery output cannot rewrite reviewed evidence.

The local SQLite fixture has no live backend, authorization, replay or
external outcome. Its result is diagnostic only even with a RUNNING WRITE.
"""

import pytest

import ark.agency.synthetic_write_plan_recovery_review as module
from ark.agency.audit import SQLiteActionAudit
from ark.agency.contracts import Effect, PlanStep, StepState, ToolCall
from ark.agency.durable_occurrence_review import SyntheticOccurrenceStore
from ark.agency.planner_journal_review import SyntheticPlanJournal
from ark.agency.registry import ToolRegistration, ToolRegistry


class NeverExecute:
    def execute(self, _call):
        raise AssertionError("recovery must never dispatch")


def _fixture(tmp_path):
    backend = NeverExecute()
    calls = (
        ToolCall("writer", "mock.write", "local", {"name": "alpha"}),
        ToolCall("writer", "mock.write", "local", {"name": "beta"}),
    )
    registry = ToolRegistry((
        ToolRegistration("writer", "mock.write", Effect.WRITE, "mock", backend),
    ))
    journal = SyntheticPlanJournal(
        tmp_path / "plan.sqlite",
        tuple(PlanStep(name, call) for name, call in zip(
            ("alpha", "beta"), calls, strict=True,
        )),
    )
    journal.append("alpha", StepState.RUNNING, expected_revision=0, at_ms=10)
    ledger_path = tmp_path / "occ.sqlite"
    SyntheticOccurrenceStore(ledger_path)
    audit = SQLiteActionAudit(tmp_path / "audit.sqlite", clock_ms=lambda: 15)
    return journal, ledger_path, audit, registry


def _equal_string(value):
    new_value = ("!" + value)[1:]
    assert new_value == value and new_value is not value
    return new_value


@pytest.mark.parametrize("mutation", ("steps", "uncertain", "digest", "prior_review"))
def test_constructor_cannot_rewrite_plan_witness_before_return(
    tmp_path, monkeypatch, mutation,
):
    fixture = _fixture(tmp_path)
    original = module.SyntheticWritePlanReview.__init__
    constructed = []

    def reflected_init(self, *args, **kwargs):
        original(self, *args, **kwargs)
        constructed.append(self)
        if mutation == "steps":
            replacement = tuple(list(self.steps))
            assert replacement == self.steps and replacement is not self.steps
            object.__setattr__(self, "steps", replacement)
        elif mutation == "uncertain":
            replacement = tuple(list(self.uncertain_step_ids))
            assert replacement == self.uncertain_step_ids
            assert replacement is not self.uncertain_step_ids
            object.__setattr__(self, "uncertain_step_ids", replacement)
        elif mutation == "digest":
            object.__setattr__(
                self, "plan_topology_digest",
                _equal_string(self.plan_topology_digest),
            )
        else:
            object.__setattr__(self.steps[0], "step_state", "succeeded")

    monkeypatch.setattr(
        module.SyntheticWritePlanReview, "__init__", reflected_init,
    )
    match = (
        "returned review changed" if mutation == "prior_review"
        else "constructed recovery result changed"
    )
    with pytest.raises(module.SyntheticWritePlanReviewRejected, match=match):
        module.review_synthetic_write_plan(*fixture)
    assert len(constructed) == 1


def test_unmodified_plan_result_remains_inert_and_marks_running_write(tmp_path):
    result = module.review_synthetic_write_plan(*_fixture(tmp_path))
    assert len(result.steps) == 2
    assert result.uncertain_step_ids == ("alpha",)
    assert result.downstream_write_hold_step_ids == ()
    assert result.dispatch_authorized is False
    assert result.automatic_replay_authorized is False
    assert result.external_outcome_known is False
