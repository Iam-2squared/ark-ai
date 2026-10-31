"""Plan-wide offline recovery must retain original scalar identity carriers.

All four stores are disposable local SQLite; no real backend execution or
external WRITE outcomes are inferred from a matching synthetic diagnosis.
"""

import pytest

import ark.agency.synthetic_write_plan_recovery_review as review
from ark.agency.audit import SQLiteActionAudit
from ark.agency.contracts import Effect, PlanStep, ToolCall
from ark.agency.durable_occurrence_review import SyntheticOccurrenceStore
from ark.agency.planner_journal_review import SyntheticPlanJournal
from ark.agency.registry import ToolRegistration, ToolRegistry


class NoDispatch:
    def execute(self, _call):
        raise AssertionError("recovery diagnosis must never call a ToolBackend")


def _fixture(tmp_path):
    call = ToolCall("writer", "mock.write", "local", {"index": 1})
    another = ToolCall("writer", "mock.write", "local", {"index": 2})
    steps = (PlanStep("alpha", call), PlanStep("beta", another))
    journal = SyntheticPlanJournal(tmp_path / "plan.sqlite", steps)
    ledger_path = tmp_path / "ledger.sqlite"
    SyntheticOccurrenceStore(ledger_path)
    audit = SQLiteActionAudit(tmp_path / "audit.sqlite", clock_ms=lambda: 11)
    registry = ToolRegistry((
        ToolRegistration("writer", "mock.write", Effect.WRITE, "fixture", NoDispatch()),
    ))
    return journal, ledger_path, audit, registry, call


@pytest.mark.parametrize("target", ("step_id", "tool", "capability", "scope"))
def test_equal_valued_scalar_swap_during_registry_bind_is_rejected(
    tmp_path, monkeypatch, target,
):
    journal, path, audit, registry, first = _fixture(tmp_path)
    original_bind = registry.bind
    step = journal._steps[0]

    def substituted_bind(call):
        bound = original_bind(call)
        if call is first:
            subject = step if target == "step_id" else call
            original = getattr(subject, target)
            clone = (original + "!")[:-1]
            assert clone == original and clone is not original
            object.__setattr__(subject, target, clone)
        return bound

    monkeypatch.setattr(registry, "bind", substituted_bind)
    with pytest.raises(
        review.SyntheticWritePlanReviewRejected, match="epoch changed",
    ):
        review.review_synthetic_write_plan(journal, path, audit, registry)


def test_unchanged_scalar_carriers_remain_disconnected_diagnostics(tmp_path):
    journal, path, audit, registry, _call = _fixture(tmp_path)
    result = review.review_synthetic_write_plan(journal, path, audit, registry)
    assert len(result.steps) == 2
    assert result.uncertain_step_ids == ()
    assert result.dispatch_authorized is False
    assert result.automatic_replay_authorized is False
    assert result.external_outcome_known is False
