"""Exact-type forged READ receipts cannot dictate detached PlanGraph progress."""

from __future__ import annotations

from dataclasses import replace

import pytest

import ark.agency.disconnected_read_cycle as cycle
from ark.agency.contracts import CapabilityGrant, Effect, PlanStep, StepState, ToolCall
from ark.agency.disconnected_read_cycle import (
    DisconnectedReadCycleRejected,
    simulate_registered_read_cycle,
)
from ark.agency.planner import PlanGraph
from ark.agency.policy import PermissionGate
from ark.agency.registry import ToolRegistration, ToolRegistry


class NeverDispatch:
    def __init__(self):
        self.calls = 0

    def execute(self, call):
        self.calls += 1
        raise AssertionError("no external dispatch permitted")


def _setup(independent=False):
    backend = NeverDispatch()
    registry = ToolRegistry((
        ToolRegistration("reader", "read.data", Effect.READ, "v1", backend),
    ))
    steps = (
        PlanStep("a", ToolCall("reader", "read.data", "local", {"x": "1"})),
        PlanStep(
            "b", ToolCall("reader", "read.data", "local", {"x": "2"}),
            () if independent else ("a",),
        ),
    )
    plan = PlanGraph(steps)
    grant = CapabilityGrant("read.data", "local", 500)
    return plan, registry, PermissionGate(), (grant,), backend


@pytest.mark.parametrize("tamper", ("omit", "substitute", "bound", "non_tuple"))
def test_forged_exact_receipt_cannot_choose_frontier_or_bound_identity(
    monkeypatch, tamper,
):
    plan, registry, gate, grants, backend = _setup(independent=True)
    original = cycle.preview_registered_read_plan

    def forged(*args, **kwargs):
        result = original(*args, **kwargs)
        if tamper == "omit":
            return replace(
                result,
                ready_step_ids=result.ready_step_ids[:1],
                ready_bound_ids=result.ready_bound_ids[:1],
            )
        if tamper == "substitute":
            return replace(result, ready_step_ids=("b", "a"))
        if tamper == "bound":
            return replace(
                result, ready_bound_ids=("f" * 64,) + result.ready_bound_ids[1:],
            )
        return replace(result, ready_step_ids=list(result.ready_step_ids))

    monkeypatch.setattr(cycle, "preview_registered_read_plan", forged)
    with pytest.raises(DisconnectedReadCycleRejected, match="receipt"):
        simulate_registered_read_cycle(
            plan, registry, gate, grants, observed_at_ms=100,
        )
    assert backend.calls == 0
    assert all(s.state is StepState.PENDING for s in plan.statuses().values())


@pytest.mark.parametrize("invalid", (True, None, -1, 2**63, 1.0, "100"))
def test_invalid_observation_never_accepted_even_when_preflight_forged(
    monkeypatch, invalid,
):
    plan, registry, gate, grants, backend = _setup()
    monkeypatch.setattr(cycle, "preview_registered_read_plan", lambda *a, **k: object())
    with pytest.raises(DisconnectedReadCycleRejected, match="exact bounded"):
        simulate_registered_read_cycle(
            plan, registry, gate, grants, observed_at_ms=invalid,
        )
    assert backend.calls == 0


def test_grant_carrier_swap_after_wave_preflight_is_refused(monkeypatch):
    plan, registry, gate, grants, backend = _setup()
    original = cycle.preview_registered_read_plan
    initial_scope = grants[0].scope
    alternate = "".join(["lo", "cal"])
    assert alternate == initial_scope and alternate is not initial_scope

    def changed_grant(*args, **kwargs):
        result = original(*args, **kwargs)
        object.__setattr__(grants[0], "scope", alternate)
        return result

    monkeypatch.setattr(cycle, "preview_registered_read_plan", changed_grant)
    with pytest.raises(DisconnectedReadCycleRejected, match="source plan changed"):
        simulate_registered_read_cycle(
            plan, registry, gate, grants, observed_at_ms=100,
        )
    assert backend.calls == 0


def test_normal_two_wave_simulation_still_preserves_original_plan():
    plan, registry, gate, grants, backend = _setup()
    before = plan.status_digest()
    receipt = simulate_registered_read_cycle(
        plan, registry, gate, grants, observed_at_ms=100,
    )
    assert len(receipt.wave_bound_step_hashes) == 2
    assert plan.status_digest() == before
    assert backend.calls == 0
    assert receipt.dispatch_authorized is False
