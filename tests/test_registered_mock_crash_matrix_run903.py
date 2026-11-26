"""Offline cross-store crash boundaries never authorize retry or real WRITE.

All files are disposable synthetic SQLite fixtures. A crash marker is not
proof of a physical side effect, user consent, or approval to dispatch.
"""

from __future__ import annotations

import hashlib

import pytest

from ark.agency.audit import SQLiteActionAudit
from ark.agency.contracts import (
    CapabilityGrant,
    Effect,
    OneShotAuthorization,
    PlanStep,
    ToolCall,
)
from ark.agency.durable_occurrence_review import SyntheticOccurrenceStore
from ark.agency.planner_journal_review import SyntheticPlanJournal
from ark.agency.policy import PermissionGate
from ark.agency.registry import ToolRegistration, ToolRegistry
from ark.agency.synthetic_mock_action_cycle_review import (
    SyntheticMockCrashInjected,
    SyntheticMockCycleRejected,
    run_synthetic_mock_cycle,
)


class NeverExecute:
    calls = 0

    def execute(self, _call):
        type(self).calls += 1
        raise AssertionError("registered backend must remain disconnected")


def _fixture(tmp_path, *, two_roots=False):
    NeverExecute.calls = 0
    backend = NeverExecute()
    first = ToolCall("synthetic.write", "write", "offline", {"root": 1})
    second = ToolCall("synthetic.write", "write", "offline", {"root": 2})
    steps = (PlanStep("a", first),)
    if two_roots:
        steps += (PlanStep("b", second),)
    registry = ToolRegistry((
        ToolRegistration("synthetic.write", "write", Effect.WRITE, "offline", backend),
    ))
    return (
        registry,
        steps,
        SyntheticPlanJournal(tmp_path / "plan.sqlite", steps),
        SyntheticOccurrenceStore(tmp_path / "occ.sqlite"),
        SQLiteActionAudit(tmp_path / "audit.sqlite", clock_ms=lambda: 12),
        first,
        second,
    )


def _cycle(fixture, call, name, fault_at=None):
    registry, _steps, journal, occurrence, audit, _first, _second = fixture
    token = OneShotAuthorization("token-" + name, call.request_id, 100)
    occurrence_id = "occ_" + hashlib.sha256(("run903-" + name).encode()).hexdigest()
    return run_synthetic_mock_cycle(
        journal, occurrence, audit, registry, call, token,
        step_id=name, occurrence_id=occurrence_id, now_ms=10,
        fault_at=fault_at,
    )


@pytest.mark.parametrize(
    ("fault", "reservations", "audits"),
    (
        ("after_running", 0, 0),
        ("after_reservation", 1, 0),
        ("after_pre_action_audit", 1, 1),
        ("after_mock_marker", 1, 1),
    ),
)
def test_each_durable_boundary_quarantines_restart_without_backend(
    tmp_path, fault, reservations, audits,
):
    fixture = _fixture(tmp_path)
    registry, steps, _journal, _occ, _audit, call, _unused = fixture
    grant = CapabilityGrant("write", "offline", 100)
    token = OneShotAuthorization("token-a", call.request_id, 100)
    assert PermissionGate().authorize_registered(
        registry, call, (grant,), now_ms=10, one_shot=token,
    ).call is call

    with pytest.raises(SyntheticMockCrashInjected, match="synthetic stop"):
        _cycle(fixture, call, "a", fault)
    # A cold reopen must observe what each independent SQLite file
    # actually committed, never the in-memory receipt that was lost.
    restarted = (
        registry,
        steps,
        SyntheticPlanJournal(tmp_path / "plan.sqlite", steps),
        SyntheticOccurrenceStore(tmp_path / "occ.sqlite"),
        SQLiteActionAudit(tmp_path / "audit.sqlite", clock_ms=lambda: 12),
        call,
        fixture[-1],
    )
    assert restarted[2].recover().ambiguous_running_steps == ("a",)
    assert restarted[3].count_synthetic() == reservations
    assert len(restarted[4].events()) == audits
    # A brand-new gate may accept a process-local token again. The durable
    # journal must independently block the repeated mock request.
    assert PermissionGate().authorize_registered(
        registry, call, (grant,), now_ms=10, one_shot=token,
    ).call is call
    with pytest.raises(SyntheticMockCycleRejected, match="cannot retry"):
        _cycle(restarted, call, "a")
    assert restarted[3].count_synthetic() == reservations
    assert len(restarted[4].events()) == audits
    assert NeverExecute.calls == 0


def test_unknown_root_does_not_replay_when_sibling_mock_completes(tmp_path):
    fixture = _fixture(tmp_path, two_roots=True)
    registry, steps, _journal, _occ, _audit, first, second = fixture
    with pytest.raises(SyntheticMockCrashInjected):
        _cycle(fixture, first, "a", "after_running")
    restarted = (
        registry,
        steps,
        SyntheticPlanJournal(tmp_path / "plan.sqlite", steps),
        SyntheticOccurrenceStore(tmp_path / "occ.sqlite"),
        SQLiteActionAudit(tmp_path / "audit.sqlite", clock_ms=lambda: 12),
        first, second,
    )
    sibling_receipt = _cycle(restarted, second, "b")
    assert sibling_receipt.dispatch_authorized is False
    assert sibling_receipt.automatic_replay_authorized is False
    assert sibling_receipt.external_outcome_known is False
    assert restarted[2].recover().ambiguous_running_steps == ("a",)
    assert restarted[3].count_synthetic() == 1
    assert len(restarted[4].events()) == 1
    with pytest.raises(SyntheticMockCycleRejected, match="cannot retry"):
        _cycle(restarted, first, "a")
    assert NeverExecute.calls == 0
