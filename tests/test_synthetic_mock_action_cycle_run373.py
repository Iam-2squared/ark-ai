"""Mock-only action-cycle fault injection never calls tool backends."""

import hashlib
from pathlib import Path

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


class MustNotExecute:
    def execute(self, call):
        raise AssertionError("no backend execution in a synthetic cycle")


def _setup(tmp_path: Path):
    call = ToolCall("fixture", "write", "local", {"operation": "fake"})
    journal = SyntheticPlanJournal(
        tmp_path / "plan.sqlite", (PlanStep("root", call),),
    )
    ledger = SyntheticOccurrenceStore(tmp_path / "ledger.sqlite")
    audit = SQLiteActionAudit(tmp_path / "audit.sqlite", clock_ms=lambda: 12)
    registry = ToolRegistry((
        ToolRegistration("fixture", "write", Effect.WRITE, "mock", MustNotExecute()),
    ))
    token = OneShotAuthorization("token-a", call.request_id, 1000)
    return journal, ledger, audit, registry, call, token


def _run(state, *, fault_at=None, occurrence="first", now=10):
    journal, ledger, audit, registry, call, token = state
    identity = "occ_" + hashlib.sha256(occurrence.encode()).hexdigest()
    return run_synthetic_mock_cycle(
        journal, ledger, audit, registry, call, token,
        step_id="root", occurrence_id=identity, now_ms=now,
        fault_at=fault_at,
    )


def test_success_is_only_a_mock_marker_with_pre_action_audit(tmp_path: Path):
    state = _setup(tmp_path)
    receipt = _run(state)
    assert receipt.step_id == "root"
    assert receipt.mock_marker.startswith("mock_")
    assert receipt.audit_event_id == 1
    assert receipt.dispatch_authorized is False
    assert receipt.automatic_replay_authorized is False
    assert receipt.external_outcome_known is False
    assert state[0].recover().step_statuses == (("root", "succeeded", 2),)
    assert state[1].count_synthetic() == 1
    assert [event.outcome for event in state[2].events()] == [
        "synthetic_audit_before_mock",
    ]
    with pytest.raises(SyntheticMockCycleRejected, match="cannot retry"):
        _run(state, occurrence="second")
    assert state[2].events()[0].event_id == receipt.audit_event_id


@pytest.mark.parametrize(("fault", "reservations", "audits"), [
    ("after_running", 0, 0),
    ("after_reservation", 1, 0),
    ("after_pre_action_audit", 1, 1),
    ("after_mock_marker", 1, 1),
])
def test_each_durable_boundary_stays_unknown_and_nonretryable(
    tmp_path: Path, fault: str, reservations: int, audits: int,
):
    state = _setup(tmp_path)
    with pytest.raises(SyntheticMockCrashInjected, match="synthetic stop"):
        _run(state, fault_at=fault)
    assert state[0].recover().ambiguous_running_steps == ("root",)
    assert state[1].count_synthetic() == reservations
    assert len(state[2].events()) == audits
    with pytest.raises(SyntheticMockCycleRejected, match="cannot retry"):
        _run(state, occurrence="different")
    assert state[1].count_synthetic() == reservations
    assert len(state[2].events()) == audits


@pytest.mark.parametrize("bad", ["unknown", "", True, 42])
def test_invalid_fault_injection_is_rejected_before_any_durable_write(
    tmp_path: Path, bad,
):
    state = _setup(tmp_path)
    with pytest.raises(SyntheticMockCycleRejected, match="exact synthetic"):
        _run(state, fault_at=bad)
    assert state[0].recover().step_statuses == (("root", "pending", 0),)
    assert state[1].count_synthetic() == 0
    assert state[2].events() == []


def test_expired_token_is_rejected_before_starting_plan(tmp_path: Path):
    state = list(_setup(tmp_path))
    state[-1] = OneShotAuthorization("expired", state[4].request_id, 10)
    with pytest.raises(SyntheticMockCycleRejected, match="expired"):
        _run(state)
    assert state[0].recover().ambiguous_running_steps == ()
    assert state[1].count_synthetic() == 0


def test_registry_effect_downgrade_is_rejected(tmp_path: Path):
    state = list(_setup(tmp_path))
    state[3] = ToolRegistry((
        ToolRegistration("fixture", "write", Effect.READ, "mock", MustNotExecute()),
    ))
    with pytest.raises(SyntheticMockCycleRejected, match="only synthetic WRITE"):
        _run(state)
    assert state[0].recover().step_statuses == (("root", "pending", 0),)
