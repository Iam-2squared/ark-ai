"""Forged detached READ preflights cannot bypass independent grant/registry checks."""

from __future__ import annotations

from dataclasses import replace

import pytest

import ark.agency.disconnected_read_cycle as cycle
from ark.agency.contracts import CapabilityGrant, Effect, PlanStep, StepState, ToolCall
from ark.agency.planner import PlanGraph
from ark.agency.policy import PermissionGate
from ark.agency.registry import ToolRegistration, ToolRegistry


class NeverDispatch:
    def __init__(self) -> None:
        self.calls = 0

    def execute(self, call):
        self.calls += 1
        raise AssertionError("synthetic READ cycle must not dispatch")


def _inputs(*, descendant_write: bool = False):
    backend = NeverDispatch()
    registrations = [
        ToolRegistration("reader", "fixture.read", Effect.READ, "fixture-v1", backend),
    ]
    steps = [
        PlanStep("a", ToolCall("reader", "fixture.read", "sandbox")),
        PlanStep("b", ToolCall("reader", "fixture.read", "sandbox", {"key": "two"}), ("a",)),
    ]
    if descendant_write:
        registrations.append(
            ToolRegistration("writer", "fixture.write", Effect.WRITE, "fixture-v1", backend)
        )
        steps[1] = PlanStep(
            "b", ToolCall("writer", "fixture.write", "sandbox"), ("a",),
        )
    return PlanGraph(tuple(steps)), ToolRegistry(tuple(registrations)), PermissionGate(), backend


@pytest.mark.parametrize(
    "grants",
    (
        (),
        (CapabilityGrant("fixture.read", "other"),),
        (CapabilityGrant("fixture.read", "sandbox", 100),),
    ),
)
def test_forged_exact_preview_cannot_skip_permission_gate(monkeypatch, grants):
    plan, registry, gate, backend = _inputs()
    receipt_type = cycle.DisconnectedReadPreflight

    def forged(*args, **kwargs):
        return receipt_type(
            plan.topology_digest(), plan.status_digest(), registry.revision,
            "a" * 64, ("a",),
            (registry.bind(plan.steps["a"].call).bound_action_id,),
            "b" * 64,
        )

    monkeypatch.setattr(cycle, "preview_registered_read_plan", forged)
    with pytest.raises(cycle.DisconnectedReadCycleRejected, match="identity recheck"):
        cycle.simulate_registered_read_cycle(
            plan, registry, gate, grants, observed_at_ms=100,
        )
    assert backend.calls == 0
    assert all(status.state is StepState.PENDING for status in plan.statuses().values())


@pytest.mark.parametrize("field", ("grant_fingerprint", "fingerprint"))
def test_forged_exact_preview_digest_cannot_be_used(monkeypatch, field):
    plan, registry, gate, backend = _inputs()
    grants = (CapabilityGrant("fixture.read", "sandbox", 500),)
    original = cycle.preview_registered_read_plan

    def forged(*args, **kwargs):
        review = original(*args, **kwargs)
        return replace(review, **{field: "f" * 64})

    monkeypatch.setattr(cycle, "preview_registered_read_plan", forged)
    with pytest.raises(cycle.DisconnectedReadCycleRejected, match="receipt"):
        cycle.simulate_registered_read_cycle(
            plan, registry, gate, grants, observed_at_ms=100,
        )
    assert backend.calls == 0


def test_forged_preflight_cannot_hide_nonready_write_descendant(monkeypatch):
    plan, registry, gate, backend = _inputs(descendant_write=True)
    grants = (CapabilityGrant("fixture.read", "sandbox", 500),)
    monkeypatch.setattr(
        cycle, "preview_registered_read_plan", lambda *args, **kwargs: object(),
    )
    with pytest.raises(cycle.DisconnectedReadCycleRejected, match="registry drift"):
        cycle.simulate_registered_read_cycle(
            plan, registry, gate, grants, observed_at_ms=100,
        )
    assert backend.calls == 0
    assert all(status.state is StepState.PENDING for status in plan.statuses().values())


def test_valid_read_cycle_still_deterministic_and_inert():
    plan, registry, gate, backend = _inputs()
    grants = (CapabilityGrant("fixture.read", "sandbox", 500),)
    first = cycle.simulate_registered_read_cycle(
        plan, registry, gate, grants, observed_at_ms=100,
    )
    second = cycle.simulate_registered_read_cycle(
        plan, registry, gate, grants, observed_at_ms=100,
    )
    assert first == second
    assert len(first.wave_bound_step_hashes) == 2
    assert first.dispatch_authorized is False
    assert backend.calls == 0
    assert all(status.state is StepState.PENDING for status in plan.statuses().values())
