"""Last Planner journal recheck must not mutate already witnessed plan evidence.

All stores are isolated disposable SQLite fixtures. No backend dispatch,
human authorization, trusted time or automatic WRITE replay is implied.
"""

import pytest

import ark.agency.synthetic_write_plan_recovery_review as plan_review
from ark.agency.audit import SQLiteActionAudit
from ark.agency.contracts import Effect, PlanStep, StepState, ToolCall
from ark.agency.durable_occurrence_review import SyntheticOccurrenceStore
from ark.agency.planner_journal_review import SyntheticPlanJournal
from ark.agency.registry import ToolRegistration, ToolRegistry


class NeverDispatch:
    def __init__(self):
        self.calls = 0

    def execute(self, _call):
        self.calls += 1
        raise AssertionError("forensic recovery must never dispatch")


def _fixture(tmp_path):
    backend = NeverDispatch()
    alpha = ToolCall("writer", "offline.write", "synthetic", {"index": 1})
    beta = ToolCall("writer", "offline.write", "synthetic", {"index": 2})
    journal = SyntheticPlanJournal(tmp_path / "plan.sqlite", (
        PlanStep("alpha", alpha),
        PlanStep("beta", beta, depends_on=("alpha",)),
    ))
    journal.append("alpha", StepState.RUNNING, expected_revision=0, at_ms=10)
    ledger = SyntheticOccurrenceStore(tmp_path / "ledger.sqlite")
    audit = SQLiteActionAudit(tmp_path / "audit.sqlite", clock_ms=lambda: 15)
    registry = ToolRegistry((
        ToolRegistration("writer", "offline.write", Effect.WRITE, "mock", backend),
    ))
    return journal, ledger._path, audit, registry, backend


def _equal_new_text(value):
    replacement = ("~" + value)[1:]
    assert replacement == value
    assert replacement is not value
    return replacement


@pytest.mark.parametrize("mutation", (
    "old_step_state",
    "old_equal_witness_digest",
    "original_equal_call_scope",
    "original_equal_dependencies",
))
def test_final_recover_cannot_rewrite_caller_or_prior_review(
    tmp_path, monkeypatch, mutation,
):
    journal, ledger, audit, registry, backend = _fixture(tmp_path)
    native_step = plan_review.review_synthetic_write_recovery
    native_recover = SyntheticPlanJournal.recover
    reviewed = []
    injected = []

    def step_wrapper(*args, **kwargs):
        result = native_step(*args, **kwargs)
        reviewed.append(result)
        return result

    def recover_wrapper(self, *args, **kwargs):
        outcome = native_recover(self, *args, **kwargs)
        # The two sorted per-step reviews plus a repeated first-step review
        # precede the final independent journal recovery.
        if len(reviewed) == 3 and not injected:
            injected.append(True)
            if mutation == "old_step_state":
                object.__setattr__(reviewed[0], "step_state", "succeeded")
            elif mutation == "old_equal_witness_digest":
                witness = reviewed[0].ledger_witness
                object.__setattr__(
                    witness, "digest", _equal_new_text(witness.digest),
                )
            elif mutation == "original_equal_call_scope":
                call = journal._steps[0].call
                object.__setattr__(call, "scope", _equal_new_text(call.scope))
            else:
                step = journal._steps[1]
                original = step.depends_on
                replacement = tuple(list(original))
                assert replacement == original
                assert replacement is not original
                object.__setattr__(step, "depends_on", replacement)
        return outcome

    monkeypatch.setattr(
        plan_review, "review_synthetic_write_recovery", step_wrapper,
    )
    monkeypatch.setattr(SyntheticPlanJournal, "recover", recover_wrapper)
    with pytest.raises(
        plan_review.SyntheticWritePlanReviewRejected,
        match="returned review changed|input epoch changed",
    ):
        plan_review.review_synthetic_write_plan(
            journal, ledger, audit, registry,
        )
    assert injected == [True]
    assert len(reviewed) == 3
    assert backend.calls == 0


def test_stable_final_recover_keeps_running_and_dependent_write_held(tmp_path):
    journal, ledger, audit, registry, backend = _fixture(tmp_path)
    result = plan_review.review_synthetic_write_plan(journal, ledger, audit, registry)
    assert result.uncertain_step_ids == ("alpha",)
    assert result.downstream_write_hold_step_ids == ("beta",)
    assert result.dispatch_authorized is False
    assert result.automatic_replay_authorized is False
    assert result.external_outcome_known is False
    assert backend.calls == 0
