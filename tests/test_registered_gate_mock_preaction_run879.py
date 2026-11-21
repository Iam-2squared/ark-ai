"""Registry-bound PermissionGate and disconnected mock WRITE chain.

These tests use only disposable local SQLite and an uncallable backend. A
process-local gate decision is never durable consent or real dispatch authority.
"""

from __future__ import annotations

import hashlib
from pathlib import Path

import pytest

from ark.agency.audit import SQLiteActionAudit
from ark.agency.contracts import (
    CapabilityGrant,
    Effect,
    OneShotAuthorization,
    PermissionDenied,
    PlanStep,
    ToolCall,
)
from ark.agency.durable_occurrence_review import SyntheticOccurrenceStore
from ark.agency.planner_journal_review import SyntheticPlanJournal
from ark.agency.policy import PermissionGate
from ark.agency.registry import BoundAction, ToolRegistration, ToolRegistry
from ark.agency.synthetic_mock_action_cycle_review import (
    SyntheticMockCrashInjected,
    SyntheticMockCycleRejected,
    run_synthetic_mock_cycle,
)


class BackendMustRemainDisconnected:
    calls = 0

    def execute(self, _call):
        type(self).calls += 1
        raise AssertionError("real registered backend must not run")


def _isolated(tmp_path: Path):
    BackendMustRemainDisconnected.calls = 0
    backend = BackendMustRemainDisconnected()
    call = ToolCall("fixture", "write", "local", {"operation": "fake"})
    registry = ToolRegistry((
        ToolRegistration("fixture", "write", Effect.WRITE, "offline", backend),
    ))
    journal = SyntheticPlanJournal(
        tmp_path / "plan.sqlite", (PlanStep("root", call),),
    )
    occurrence = SyntheticOccurrenceStore(tmp_path / "occurrence.sqlite")
    audit = SQLiteActionAudit(tmp_path / "audit.sqlite", clock_ms=lambda: 12)
    grant = CapabilityGrant("write", "local", 100)
    token = OneShotAuthorization("run879-token", call.request_id, 100)
    identity = "occ_" + hashlib.sha256(b"run879-write").hexdigest()
    return journal, occurrence, audit, registry, call, grant, token, identity


def _mock(state, *, fault_at=None):
    journal, occurrence, audit, registry, call, _grant, token, identity = state
    return run_synthetic_mock_cycle(
        journal, occurrence, audit, registry, call, token,
        step_id="root", occurrence_id=identity, now_ms=10, fault_at=fault_at,
    )


def test_registry_gate_then_durable_preaction_is_still_mock_only(tmp_path: Path):
    state = _isolated(tmp_path)
    journal, occurrence, audit, registry, call, grant, token, _identity = state
    gate = PermissionGate()
    bound = gate.authorize_registered(
        registry, call, (grant,), now_ms=10, one_shot=token,
    )
    assert type(bound) is BoundAction
    assert bound.registration is registry.get("fixture")
    assert bound.call is call
    receipt = _mock(state)
    assert receipt.dispatch_authorized is False
    assert receipt.external_outcome_known is False
    assert receipt.automatic_replay_authorized is False
    assert BackendMustRemainDisconnected.calls == 0
    assert journal.recover().step_statuses == (("root", "succeeded", 2),)
    assert occurrence.count_synthetic() == 1
    assert [row.outcome for row in audit.events()] == [
        "synthetic_audit_before_mock",
    ]
    with pytest.raises(PermissionDenied, match="consumed"):
        gate.authorize_registered(
            registry, call, (grant,), now_ms=10, one_shot=token,
        )


def test_denied_grant_never_reaches_journal_or_audit(tmp_path: Path):
    state = _isolated(tmp_path)
    journal, occurrence, audit, registry, call, _grant, token, _identity = state
    gate = PermissionGate()
    with pytest.raises(PermissionDenied, match="no active exact-scope"):
        gate.authorize_registered(
            registry, call, (CapabilityGrant("write", "other", 100),),
            now_ms=10, one_shot=token,
        )
    assert journal.recover().step_statuses == (("root", "pending", 0),)
    assert occurrence.count_synthetic() == 0
    assert audit.events() == []
    assert BackendMustRemainDisconnected.calls == 0


def test_new_process_local_gate_cannot_replay_durable_unknown(
    tmp_path: Path,
):
    state = _isolated(tmp_path)
    journal, occurrence, audit, registry, call, grant, token, _identity = state
    PermissionGate().authorize_registered(
        registry, call, (grant,), now_ms=10, one_shot=token,
    )
    with pytest.raises(SyntheticMockCrashInjected, match="synthetic stop"):
        _mock(state, fault_at="after_pre_action_audit")
    assert journal.recover().ambiguous_running_steps == ("root",)
    assert occurrence.count_synthetic() == 1
    assert len(audit.events()) == 1
    # A newly constructed process-local gate forgets its consumed-token set.
    # This is NOT a durable approval and cannot override the journal's
    # permanently ambiguous, no-retry mock WRITE.
    rebound = PermissionGate().authorize_registered(
        registry, call, (grant,), now_ms=10, one_shot=token,
    )
    assert rebound.call is call
    with pytest.raises(SyntheticMockCycleRejected, match="cannot retry"):
        _mock(state)
    assert journal.recover().ambiguous_running_steps == ("root",)
    assert occurrence.count_synthetic() == 1
    assert len(audit.events()) == 1
    assert BackendMustRemainDisconnected.calls == 0
