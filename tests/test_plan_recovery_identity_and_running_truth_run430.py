"""A plan-wide read cannot trust a reentrant per-step recovery's claims.

The registry and recovered RUNNING state are independent local fixtures.
Every test is disconnected, never executes tools and never authorizes replay.
"""

import pytest

import ark.agency.synthetic_write_plan_recovery_review as review_module
from ark.agency.audit import SQLiteActionAudit
from ark.agency.contracts import Effect, PlanStep, StepState, ToolCall
from ark.agency.durable_occurrence_review import SyntheticOccurrenceStore
from ark.agency.planner_journal_review import SyntheticPlanJournal
from ark.agency.registry import ToolRegistration, ToolRegistry


class NoDispatch:
    def __init__(self):
        self.calls = 0

    def execute(self, _call):
        self.calls += 1
        raise AssertionError("a disconnected recovery diagnosis cannot execute a tool")


def _state(tmp_path, *, running):
    call = ToolCall("writer", "offline.write", "synthetic", {"purpose": "test"})
    journal = SyntheticPlanJournal(
        tmp_path / "plan.sqlite", (PlanStep("write", call),),
    )
    if running:
        journal.append("write", StepState.RUNNING, expected_revision=0, at_ms=10)
    ledger = SyntheticOccurrenceStore(tmp_path / "occurrences.sqlite")
    audit = SQLiteActionAudit(tmp_path / "audit.sqlite", clock_ms=lambda: 20)
    backend = NoDispatch()
    registry = ToolRegistry((
        ToolRegistration("writer", "offline.write", Effect.WRITE, "mock", backend),
    ))
    return journal, ledger._path, audit, registry, backend


@pytest.mark.parametrize("running", (False, True))
@pytest.mark.parametrize("forgery", ("bound_action_id", "ambiguous_write"))
def test_plan_review_rejects_per_step_bound_or_running_forgery(
    tmp_path, monkeypatch, running, forgery,
):
    state = _state(tmp_path, running=running)
    native = review_module.review_synthetic_write_recovery
    called = []

    def forged(*args, **kwargs):
        result = native(*args, **kwargs)
        called.append(True)
        if forgery == "bound_action_id":
            object.__setattr__(result, "bound_action_id", "bound_" + "0" * 64)
        else:
            object.__setattr__(result, "ambiguous_write", not result.ambiguous_write)
        return result

    monkeypatch.setattr(review_module, "review_synthetic_write_recovery", forged)
    with pytest.raises(
        review_module.SyntheticWritePlanReviewRejected,
        match="synthetic per-step recovery differs from original plan",
    ):
        review_module.review_synthetic_write_plan(*state[:4])
    assert called == [True]
    assert state[4].calls == 0


@pytest.mark.parametrize("running", (False, True))
def test_unmodified_per_step_bound_identity_and_uncertainty_remain_inert(
    tmp_path, running,
):
    state = _state(tmp_path, running=running)
    result = review_module.review_synthetic_write_plan(*state[:4])
    assert len(result.steps) == 1
    item = result.steps[0]
    assert item.bound_action_id == state[3].bind(
        state[0]._steps[0].call,
    ).bound_action_id
    assert item.ambiguous_write is running
    assert result.uncertain_step_ids == (("write",) if running else ())
    assert result.dispatch_authorized is False
    assert result.automatic_replay_authorized is False
    assert result.external_outcome_known is False
    assert state[4].calls == 0
