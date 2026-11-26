"""Nonempty audit-link evidence survives simulated multi-WRITE restarts.

These fixtures commit only disposable SQLite records. They never dispatch a
backend, authenticate an issuer, or prove external side-effect completion.
"""

import pytest

from ark.agency.audit import SQLiteActionAudit
from ark.agency.contracts import (
    Effect,
    OneShotAuthorization,
    PlanStep,
    ToolCall,
)
from ark.agency.durable_occurrence_review import SyntheticOccurrenceStore
from ark.agency.planner_journal_review import SyntheticPlanJournal
from ark.agency.registry import ToolRegistration, ToolRegistry
from ark.agency.synthetic_mock_action_cycle_review import (
    SyntheticMockCrashInjected,
    SyntheticMockCycleRejected,
    run_synthetic_mock_cycle,
)
from ark.agency.synthetic_occurrence_audit_link_review import (
    SyntheticOccurrenceAuditLinkStore,
)
from ark.agency.synthetic_recovery_triage import SyntheticRecoveryRejected
from ark.agency.synthetic_write_plan_recovery_review import (
    review_synthetic_write_plan,
)


class NoDispatch:
    def __init__(self):
        self.calls = 0

    def execute(self, _call):
        self.calls += 1
        raise AssertionError("real action forbidden in disconnected fixtures")


def _fixture(root, *, dependent=False):
    root.mkdir(parents=True, exist_ok=True)
    backend = NoDispatch()
    calls = (
        ToolCall("writer", "mock.write", "local", {"step": "alpha"}),
        ToolCall("writer", "mock.write", "local", {"step": "beta"}),
    )
    journal = SyntheticPlanJournal(root / "plan.sqlite", (
        PlanStep("alpha", calls[0]),
        PlanStep("beta", calls[1], ("alpha",) if dependent else ()),
    ))
    ledger = SyntheticOccurrenceStore(root / "ledger.sqlite")
    audit = SQLiteActionAudit(root / "audit.sqlite", clock_ms=lambda: 15)
    link = SyntheticOccurrenceAuditLinkStore(root / "link.sqlite")
    registry = ToolRegistry((
        ToolRegistration("writer", "mock.write", Effect.WRITE, "mock", backend),
    ))
    return journal, ledger, audit, link, registry, calls, backend


def _review(state, **kwargs):
    journal, ledger, audit, link, registry, _calls, backend = state
    result = review_synthetic_write_plan(
        journal, ledger._path, audit, registry, link_store=link, **kwargs,
    )
    assert backend.calls == 0
    assert result.dispatch_authorized is False
    assert result.external_outcome_known is False
    assert result.automatic_replay_authorized is False
    return result


def _retain(review):
    first = review.steps[0]
    return dict(
        retained_plan=first.plan_tail,
        retained_ledger=first.ledger_witness,
        retained_audit=first.audit_witness,
        retained_link=first.link_witness,
    )


def _fault_linked(state, index):
    journal, ledger, audit, links, registry, calls, _backend = state
    call = calls[index]
    name = ("alpha", "beta")[index]
    token = OneShotAuthorization(
        "synthetic-token-" + name, call.request_id, 1000,
    )
    with pytest.raises(SyntheticMockCrashInjected, match="after audit link"):
        run_synthetic_mock_cycle(
            journal, ledger, audit, registry, call, token,
            step_id=name, occurrence_id="occ_" + str(index + 1) * 64,
            now_ms=10 + index,
            fault_at="after_audit_link", link_store=links,
        )


def test_two_linked_unknown_writes_retain_all_four_histories_across_restart(tmp_path):
    initial = _fixture(tmp_path)
    _fault_linked(initial, 0)
    _fault_linked(initial, 1)
    observed = _review(initial)
    assert observed.uncertain_step_ids == ("alpha", "beta")
    assert observed.steps[0].link_witness.event_count == 2
    assert all(len(step.matching_audit_links) == 1 for step in observed.steps)
    assert all(step.step_state == "running" for step in observed.steps)
    assert observed.downstream_write_hold_step_ids == ()

    reopened = _fixture(tmp_path)
    again = _review(reopened, **_retain(observed))
    assert again == observed
    for index in (0, 1):
        call = reopened[5][index]
        with pytest.raises(SyntheticMockCycleRejected, match="not PENDING"):
            run_synthetic_mock_cycle(
                reopened[0], reopened[1], reopened[2],
                reopened[4], call,
                OneShotAuthorization("again-" + str(index), call.request_id, 1000),
                step_id=("alpha", "beta")[index],
                occurrence_id="occ_" + str(index + 1) * 64,
                now_ms=20, link_store=reopened[3],
            )
    assert reopened[6].calls == 0


def test_nonempty_retained_link_cannot_disappear_into_empty_replacement(tmp_path):
    original = _fixture(tmp_path / "original")
    _fault_linked(original, 0)
    observed = _review(original)
    assert observed.steps[0].link_witness.event_count == 1

    replacement = _fixture(tmp_path / "replacement")
    assert _review(replacement).uncertain_step_ids == ()
    with pytest.raises(SyntheticRecoveryRejected, match="retained.*link"):
        _review(replacement, retained_link=observed.steps[0].link_witness)
    assert replacement[6].calls == 0


def test_pending_write_with_linked_reservation_holds_dependent_write(tmp_path):
    state = _fixture(tmp_path, dependent=True)
    journal, ledger, audit, links, registry, calls, backend = state
    call = calls[0]
    reservation = ledger.reserve_synthetic(
        registry, call,
        OneShotAuthorization("disconnected", call.request_id, 1000),
        occurrence_id="occ_" + "e" * 64, now_ms=10,
    )
    event = audit.append(call, outcome="synthetic_audit_before_mock")
    links.link_synthetic(
        registry, call, ledger, reservation, audit, event, at_ms=15,
    )

    result = _review(state)
    assert result.steps[0].step_state == "pending"
    assert result.steps[0].ambiguous_write is False
    assert result.uncertain_step_ids == ("alpha",)
    assert result.downstream_write_hold_step_ids == ("beta",)
    assert result.steps[0].link_witness.event_count == 1
    assert backend.calls == 0
