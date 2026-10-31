"""Final-result and recovered-witness custody for disconnected WRITE triage.

The fixture is local SQLite only; neither review nor mutation may execute a backend.
"""

import pytest

import ark.agency.synthetic_recovery_triage as triage
from ark.agency.audit import SQLiteActionAudit
from ark.agency.contracts import Effect, PlanStep, ToolCall
from ark.agency.durable_occurrence_review import SyntheticOccurrenceStore
from ark.agency.planner_journal_review import SyntheticPlanJournal
from ark.agency.registry import ToolRegistration, ToolRegistry


class NoDispatch:
    def __init__(self):
        self.calls = 0

    def execute(self, _call):
        self.calls += 1
        raise AssertionError("synthetic triage must not dispatch")


def _setup(tmp_path):
    call = ToolCall("writer", "offline.write", "local", {"ordinal": 1})
    journal = SyntheticPlanJournal(
        tmp_path / "plan.sqlite", (PlanStep("first", call),),
    )
    ledger = tmp_path / "ledger.sqlite"
    SyntheticOccurrenceStore(ledger)
    audit = SQLiteActionAudit(tmp_path / "audit.sqlite", clock_ms=lambda: 17)
    backend = NoDispatch()
    registry = ToolRegistry((
        ToolRegistration("writer", "offline.write", Effect.WRITE, "mock", backend),
    ))
    return journal, ledger, audit, registry, call, backend


def _clone(value):
    duplicate = ("!" + value)[1:]
    assert duplicate == value and duplicate is not value
    return duplicate


@pytest.mark.parametrize("variant", (
    "wrong_result_type",
    "forged_step_state",
    "replaced_tail_carrier",
    "replaced_caller_tool",
    "replaced_bound_identity",
))
def test_result_constructor_must_not_change_original_recovery_evidence(
    tmp_path, monkeypatch, variant,
):
    journal, ledger, audit, registry, call, backend = _setup(tmp_path)
    original_result = triage.SyntheticRecoveryReview
    original_bind = ToolRegistry.bind
    captured = []
    constructors = []

    def capture_bind(self, requested):
        bound = original_bind(self, requested)
        captured.append(bound)
        return bound

    monkeypatch.setattr(ToolRegistry, "bind", capture_bind)

    def injected_constructor(*args):
        constructors.append(variant)
        if variant == "wrong_result_type":
            return object()
        result = original_result(*args)
        if variant == "forged_step_state":
            object.__setattr__(result, "step_state", "succeeded")
        elif variant == "replaced_tail_carrier":
            original = result.plan_tail.status_digest
            object.__setattr__(result.plan_tail, "status_digest", _clone(original))
        elif variant == "replaced_caller_tool":
            object.__setattr__(call, "tool", _clone(call.tool))
        elif variant == "replaced_bound_identity":
            bound = captured[0]
            object.__setattr__(
                bound, "bound_action_id", _clone(bound.bound_action_id),
            )
        return result

    monkeypatch.setattr(triage, "SyntheticRecoveryReview", injected_constructor)
    with pytest.raises(triage.SyntheticRecoveryRejected):
        triage.review_synthetic_write_recovery(
            journal, ledger, audit, registry, call, step_id="first",
        )
    assert constructors == [variant]
    assert backend.calls == 0


def test_unmodified_review_result_remains_exact_and_deny_only(tmp_path):
    journal, ledger, audit, registry, call, backend = _setup(tmp_path)
    review = triage.review_synthetic_write_recovery(
        journal, ledger, audit, registry, call, step_id="first",
    )
    assert type(review) is triage.SyntheticRecoveryReview
    assert review.step_state == "pending"
    assert review.matching_occurrences == ()
    assert review.dispatch_authorized is False
    assert review.automatic_replay_authorized is False
    assert review.external_outcome_known is False
    assert backend.calls == 0
