"""Preflight and final mock READ cycle are non-authorizing receipts only."""

from __future__ import annotations

import pytest

from ark.agency.contracts import CapabilityGrant, Effect, PlanStep, ToolCall
from ark.agency.disconnected_read_cycle import (
    DisconnectedReadCycleReceipt,
    DisconnectedReadCycleRejected,
    simulate_registered_read_cycle,
)
from ark.agency.disconnected_read_preflight import DisconnectedReadPreflight
from ark.agency.planner import PlanGraph
from ark.agency.policy import PermissionGate
from ark.agency.registry import ToolRegistration, ToolRegistry


class NoDispatchBackend:
    def __init__(self):
        self.calls = 0

    def execute(self, call):
        self.calls += 1
        raise AssertionError("never dispatch fixture backend")


def _fixture():
    backend = NoDispatchBackend()
    registry = ToolRegistry((
        ToolRegistration("read", "fixture.read", Effect.READ, "offline", backend),
    ))
    step = PlanStep(
        "a", ToolCall("read", "fixture.read", "local", {"value": 1}),
    )
    plan = PlanGraph((step,))
    return plan, registry, PermissionGate(), (
        CapabilityGrant("fixture.read", "local", 500),
    ), backend


def _cycle(fixture):
    plan, registry, gate, grants, _backend = fixture
    return simulate_registered_read_cycle(
        plan, registry, gate, grants, observed_at_ms=100,
    )


@pytest.mark.parametrize(
    "field",
    (
        "external_result_verified",
        "authenticated_clock_or_consent",
        "automatic_replay_authorized",
    ),
)
def test_forged_preflight_authority_refuses_shadow_transition(monkeypatch, field):
    fixture = _fixture()
    monkeypatch.setattr(
        DisconnectedReadPreflight, field, property(lambda _value: True),
    )
    with pytest.raises(DisconnectedReadCycleRejected, match="receipt"):
        _cycle(fixture)
    assert fixture[-1].calls == 0


@pytest.mark.parametrize(
    "field",
    (
        "dispatch_authorized",
        "external_result_verified",
        "automatic_replay_authorized",
        "authenticated_clock_or_consent",
    ),
)
def test_forged_final_receipt_authority_refuses_result(monkeypatch, field):
    fixture = _fixture()
    original_status = fixture[0].status_digest()
    monkeypatch.setattr(
        DisconnectedReadCycleReceipt, field, property(lambda _value: 1),
    )
    with pytest.raises(DisconnectedReadCycleRejected, match="receipt changed"):
        _cycle(fixture)
    assert fixture[0].status_digest() == original_status
    assert fixture[-1].calls == 0


def test_ordinary_cycle_stays_inert():
    fixture = _fixture()
    receipt = _cycle(fixture)
    assert receipt.dispatch_authorized is False
    assert receipt.external_result_verified is False
    assert receipt.automatic_replay_authorized is False
    assert receipt.authenticated_clock_or_consent is False
    assert fixture[-1].calls == 0
