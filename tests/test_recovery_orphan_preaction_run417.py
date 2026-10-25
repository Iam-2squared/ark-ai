"""Offline orphan-audit recovery must never classify a missing reservation as clean.

Every database here is disposable; no backend is dispatched and no audit
receipt attests an external effect or unlocks a WRITE retry.
"""

import sqlite3

import pytest

from ark.agency.audit import SQLiteActionAudit
from ark.agency.contracts import (
    Effect,
    OneShotAuthorization,
    PlanStep,
    StepState,
    ToolCall,
)
from ark.agency.durable_occurrence_review import SyntheticOccurrenceStore
from ark.agency.planner_journal_review import SyntheticPlanJournal
from ark.agency.registry import ToolRegistration, ToolRegistry
from ark.agency.synthetic_recovery_triage import (
    SyntheticRecoveryRejected,
    review_synthetic_write_recovery,
)
from ark.agency.synthetic_write_plan_recovery_review import (
    review_synthetic_write_plan,
)


class NeverDispatch:
    def __init__(self):
        self.calls = 0

    def execute(self, _call):
        self.calls += 1
        raise AssertionError("recovery may not dispatch tools")


def _fixture(tmp_path, *, two=False):
    call = ToolCall("writer", "mock.write", "offline", {"step": 1})
    other = ToolCall("writer", "mock.write", "offline", {"step": 2})
    steps = (PlanStep("root", call),)
    if two:
        steps += (PlanStep("independent", other),)
    journal = SyntheticPlanJournal(tmp_path / "plan.sqlite", steps)
    ledger = SyntheticOccurrenceStore(tmp_path / "ledger.sqlite")
    audit = SQLiteActionAudit(tmp_path / "audit.sqlite", clock_ms=lambda: 12)
    backend = NeverDispatch()
    registry = ToolRegistry((
        ToolRegistration("writer", "mock.write", Effect.WRITE, "offline", backend),
    ))
    return journal, ledger, audit, registry, call, other, backend


def _review(state):
    journal, ledger, audit, registry, call, _other, backend = state
    try:
        return review_synthetic_write_recovery(
            journal, ledger._path, audit, registry, call, step_id="root",
        )
    finally:
        assert backend.calls == 0


@pytest.mark.parametrize("state", (
    StepState.PENDING,
    StepState.RUNNING,
    StepState.SUCCEEDED,
))
def test_orphan_preaction_audit_denied_without_retained_witness(tmp_path, state):
    case = _fixture(tmp_path)
    if state is not StepState.PENDING:
        case[0].append("root", StepState.RUNNING, expected_revision=0, at_ms=10)
    if state is StepState.SUCCEEDED:
        case[0].append("root", StepState.SUCCEEDED, expected_revision=1, at_ms=11)
    case[2].append(case[4], outcome="synthetic_audit_before_mock")
    assert case[1].count_synthetic() == 0
    with pytest.raises(SyntheticRecoveryRejected, match="lacks durable reservation"):
        _review(case)
    assert case[1].count_synthetic() == 0
    assert case[6].calls == 0


def test_partial_ledger_erasure_refused_even_without_caller_retained_history(tmp_path):
    case = _fixture(tmp_path)
    call = case[4]
    case[1].reserve_synthetic(
        case[3], call, OneShotAuthorization("one", call.request_id, 1000),
        occurrence_id="occ_" + "a" * 64, now_ms=10,
    )
    case[2].append(call, outcome="synthetic_audit_before_mock")
    assert _review(case).matching_occurrences == ("occ_" + "a" * 64,)
    with sqlite3.connect(case[1]._path) as conn:
        conn.execute("DELETE FROM synthetic_occurrence_reservations")
    with pytest.raises(SyntheticRecoveryRejected, match="lacks durable reservation"):
        _review(case)
    assert case[6].calls == 0


def test_other_request_preaction_audit_does_not_taint_unrelated_write(tmp_path):
    case = _fixture(tmp_path, two=True)
    case[2].append(case[5], outcome="synthetic_audit_before_mock")
    result = _review(case)
    assert result.step_state == "pending"
    assert result.matching_occurrences == ()
    assert result.external_outcome_known is False
    assert result.automatic_replay_authorized is False
    assert case[6].calls == 0


def test_matching_reservation_and_preaction_audit_remain_inert(tmp_path):
    case = _fixture(tmp_path)
    call = case[4]
    receipt = case[1].reserve_synthetic(
        case[3], call, OneShotAuthorization("one", call.request_id, 1000),
        occurrence_id="occ_" + "b" * 64, now_ms=10,
    )
    case[2].append(call, outcome="synthetic_audit_before_mock")
    result = _review(case)
    assert result.matching_occurrences == (receipt.occurrence_id,)
    assert result.external_outcome_known is False
    assert result.automatic_replay_authorized is False
    assert case[6].calls == 0


def test_planwide_orphan_preaction_denied_without_replay(tmp_path):
    case = _fixture(tmp_path, two=True)
    case[2].append(case[4], outcome="synthetic_audit_before_mock")
    with pytest.raises(SyntheticRecoveryRejected, match="lacks durable reservation"):
        review_synthetic_write_plan(
            case[0], case[1]._path, case[2], case[3],
        )
    assert case[6].calls == 0
