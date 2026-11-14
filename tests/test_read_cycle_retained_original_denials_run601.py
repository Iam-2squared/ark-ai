"""Retained READ-cycle verification refuses false-looking authority shims.

Only disconnected mock simulation is used: no backend, consent proof or replay.
"""

from __future__ import annotations

from dataclasses import replace

import pytest

import ark.agency.disconnected_read_cycle_receipt_recheck as recheck
from ark.agency.contracts import (
    CapabilityGrant,
    Effect,
    PlanStep,
    StepState,
    ToolCall,
)
from ark.agency.disconnected_read_cycle import simulate_registered_read_cycle
from ark.agency.planner import PlanGraph
from ark.agency.policy import PermissionGate
from ark.agency.registry import ToolRegistration, ToolRegistry

_FLAGS = (
    "dispatch_authorized", "external_result_verified",
    "automatic_replay_authorized", "authenticated_clock_or_consent",
)


class NeverExecute:
    def __init__(self):
        self.calls = 0

    def execute(self, call):
        self.calls += 1
        raise AssertionError("retained offline READ verifier dispatched a backend")


def _inputs():
    backend = NeverExecute()
    registry = ToolRegistry((
        ToolRegistration("reader", "local.read", Effect.READ, "fixture", backend),
    ))
    plan = PlanGraph((
        PlanStep("a", ToolCall("reader", "local.read", "private")),
        PlanStep("b", ToolCall("reader", "local.read", "private"), ("a",)),
    ))
    gate = PermissionGate()
    grants = (CapabilityGrant("local.read", "private", 500),)
    return plan, registry, gate, grants, backend


def _receipt(plan, registry, gate, grants):
    return simulate_registered_read_cycle(
        plan, registry, gate, grants, observed_at_ms=100,
    )


@pytest.mark.parametrize("flag", _FLAGS)
@pytest.mark.parametrize("moment", ("entry", "after_fresh_simulation"))
def test_retained_verifier_never_invokes_false_looking_replacement(
    monkeypatch, flag, moment,
):
    plan, registry, gate, grants, backend = _inputs()
    receipt = _receipt(plan, registry, gate, grants)
    original_status = plan.status_digest()
    getter_calls = []

    def counterfeit(self):
        getter_calls.append(flag)
        return False

    def substitute():
        monkeypatch.setattr(
            recheck.DisconnectedReadCycleReceipt, flag, property(counterfeit),
        )

    if moment == "entry":
        substitute()
    else:
        original_simulator = recheck.simulate_registered_read_cycle

        def altered(*args, **kwargs):
            fresh = original_simulator(*args, **kwargs)
            substitute()
            return fresh

        monkeypatch.setattr(recheck, "simulate_registered_read_cycle", altered)

    with pytest.raises(
        recheck.DisconnectedReadCycleReceiptRejected,
        match="denial descriptor substituted",
    ):
        recheck.verify_disconnected_read_cycle_receipt(
            receipt, plan, registry, gate, grants, observed_at_ms=100,
        )

    assert getter_calls == []
    assert backend.calls == 0
    assert gate._consumed_tokens == set()
    assert plan.status_digest() == original_status
    assert all(item.state is StepState.PENDING for item in plan.statuses().values())


def test_original_retained_receipt_still_checks_both_inert_waves():
    plan, registry, gate, grants, backend = _inputs()
    # Reconstructing an inert diagnostic is allowed; it confers no provenance.
    receipt = replace(_receipt(plan, registry, gate, grants))
    assert len(receipt.wave_bound_step_hashes) == 2
    assert recheck.verify_disconnected_read_cycle_receipt(
        receipt, plan, registry, gate, grants, observed_at_ms=100,
    ) is None
    assert backend.calls == 0
    assert not gate._consumed_tokens
    assert all(item.state is StepState.PENDING for item in plan.statuses().values())
