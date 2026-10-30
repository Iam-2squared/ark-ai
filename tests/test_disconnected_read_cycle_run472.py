"""End-to-end READ-only DAG simulation uses no backend or durable action."""

from __future__ import annotations

from dataclasses import replace

import pytest

import ark.agency.disconnected_read_cycle as cycle
from ark.agency.contracts import (
    CapabilityGrant,
    Effect,
    PlanStep,
    StepState,
    ToolCall,
)
from ark.agency.disconnected_read_cycle import (
    DisconnectedReadCycleRejected,
    simulate_registered_read_cycle,
)
from ark.agency.planner import PlanGraph
from ark.agency.policy import PermissionGate
from ark.agency.registry import ToolRegistration, ToolRegistry


class ExplosiveBackend:
    def __init__(self) -> None:
        self.calls = 0

    def execute(self, call: ToolCall) -> object:
        self.calls += 1
        raise AssertionError("disconnected READ simulation must not dispatch")


def _setup(
    *,
    independent: bool = False,
    effect: Effect = Effect.READ,
    expiry: int | None = 500,
):
    backend = ExplosiveBackend()
    registry = ToolRegistry((
        ToolRegistration("reader", "fixture.read", effect, "offline-v1", backend),
    ))
    first = PlanStep(
        "a", ToolCall("reader", "fixture.read", "sandbox", {"secret": "canary"})
    )
    second = PlanStep(
        "b", ToolCall("reader", "fixture.read", "sandbox", {"item": 2}),
        () if independent else ("a",),
    )
    plan = PlanGraph((second, first))
    grant = CapabilityGrant("fixture.read", "sandbox", expiry)
    return plan, registry, PermissionGate(), (grant,), backend


def test_simulates_two_dependency_waves_without_backend_execution():
    plan, registry, gate, grants, backend = _setup()
    original = plan.status_digest()
    receipt = simulate_registered_read_cycle(
        plan, registry, gate, grants, observed_at_ms=100,
    )
    assert len(receipt.wave_bound_step_hashes) == 2
    assert [len(wave) for wave in receipt.wave_bound_step_hashes] == [1, 1]
    assert all(len(ident) == 64 for wave in receipt.wave_bound_step_hashes for ident in wave)
    assert receipt.topology_digest == plan.topology_digest()
    assert receipt.final_status_digest != original
    assert plan.status_digest() == original
    assert all(status.state is StepState.PENDING for status in plan.statuses().values())
    assert backend.calls == 0
    assert receipt.dispatch_authorized is False
    assert receipt.external_result_verified is False
    assert receipt.automatic_replay_authorized is False
    assert receipt.authenticated_clock_or_consent is False
    assert "canary" not in repr(receipt)


def test_independent_reads_form_one_deterministic_wave():
    plan, registry, gate, grants, backend = _setup(independent=True)
    first = simulate_registered_read_cycle(
        plan, registry, gate, grants, observed_at_ms=100,
    )
    second = simulate_registered_read_cycle(
        plan, registry, gate, grants, observed_at_ms=100,
    )
    assert first == second
    assert len(first.wave_bound_step_hashes) == 1
    assert len(first.wave_bound_step_hashes[0]) == 2
    assert backend.calls == 0


@pytest.mark.parametrize("observed_at_ms", (99, 100, 101))
def test_digest_binds_clock_sample_but_never_authenticates_it(observed_at_ms):
    plan, registry, gate, grants, backend = _setup()
    result = simulate_registered_read_cycle(
        plan, registry, gate, grants, observed_at_ms=observed_at_ms,
    )
    assert len(result.fingerprint) == 64
    assert result.authenticated_clock_or_consent is False
    assert backend.calls == 0


def test_different_clock_changes_result_digest():
    plan, registry, gate, grants, _ = _setup()
    first = simulate_registered_read_cycle(plan, registry, gate, grants, observed_at_ms=100)
    second = simulate_registered_read_cycle(plan, registry, gate, grants, observed_at_ms=101)
    assert first.fingerprint != second.fingerprint


@pytest.mark.parametrize("effect", (Effect.WRITE,))
def test_refuses_any_write_effect_before_mock_transitions(effect):
    plan, registry, gate, grants, backend = _setup(effect=effect)
    with pytest.raises(DisconnectedReadCycleRejected, match="preflight"):
        simulate_registered_read_cycle(plan, registry, gate, grants, observed_at_ms=100)
    assert backend.calls == 0
    assert all(status.state is StepState.PENDING for status in plan.statuses().values())


@pytest.mark.parametrize("expiry", (99, 100))
def test_expired_grants_deny_entire_cycle(expiry):
    plan, registry, gate, _, backend = _setup(expiry=expiry)
    grants = (CapabilityGrant("fixture.read", "sandbox", expiry),)
    with pytest.raises(DisconnectedReadCycleRejected, match="preflight"):
        simulate_registered_read_cycle(plan, registry, gate, grants, observed_at_ms=100)
    assert backend.calls == 0


def test_wrong_scope_grant_is_not_authority():
    plan, registry, gate, _, backend = _setup()
    grants = (CapabilityGrant("fixture.read", "other"),)
    with pytest.raises(DisconnectedReadCycleRejected, match="preflight"):
        simulate_registered_read_cycle(plan, registry, gate, grants, observed_at_ms=100)
    assert backend.calls == 0


def test_nonfresh_plan_does_not_replay():
    plan, registry, gate, grants, backend = _setup()
    plan.transition("a", StepState.RUNNING, expected_revision=0)
    with pytest.raises(DisconnectedReadCycleRejected, match="fresh pending"):
        simulate_registered_read_cycle(plan, registry, gate, grants, observed_at_ms=100)
    assert backend.calls == 0


def test_reentrant_gate_mutates_original_plan_and_fails_closed(monkeypatch):
    plan, registry, gate, grants, backend = _setup()
    original_gate = PermissionGate.authorize_registered

    def changing_gate(self, registry, call, grants, *, now_ms, one_shot=None):
        bound = original_gate(
            self, registry, call, grants, now_ms=now_ms, one_shot=one_shot,
        )
        plan.transition("a", StepState.RUNNING, expected_revision=0)
        return bound

    monkeypatch.setattr(PermissionGate, "authorize_registered", changing_gate)
    with pytest.raises(DisconnectedReadCycleRejected, match="source plan changed"):
        simulate_registered_read_cycle(plan, registry, gate, grants, observed_at_ms=100)
    assert backend.calls == 0


def test_forged_preflight_result_cannot_advance_mock(monkeypatch):
    plan, registry, gate, grants, backend = _setup()
    monkeypatch.setattr(cycle, "preview_registered_read_plan", lambda *a, **kw: object())
    with pytest.raises(DisconnectedReadCycleRejected, match="receipt"):
        simulate_registered_read_cycle(plan, registry, gate, grants, observed_at_ms=100)
    assert backend.calls == 0


def test_forged_transition_result_is_refused(monkeypatch):
    plan, registry, gate, grants, backend = _setup()
    original_transition = PlanGraph.transition

    def forged_transition(self, step_id, to_state, *, expected_revision):
        result = original_transition(
            self, step_id, to_state, expected_revision=expected_revision,
        )
        return replace(result, revision=7)

    monkeypatch.setattr(PlanGraph, "transition", forged_transition)
    with pytest.raises(DisconnectedReadCycleRejected, match="transition result"):
        simulate_registered_read_cycle(plan, registry, gate, grants, observed_at_ms=100)
    assert backend.calls == 0


@pytest.mark.parametrize("invalid", (None, {}, ["grant"], (object(),)))
def test_invalid_grants_never_result_in_a_mock_action(invalid):
    plan, registry, gate, _, backend = _setup()
    with pytest.raises(DisconnectedReadCycleRejected):
        simulate_registered_read_cycle(
            plan, registry, gate, invalid, observed_at_ms=100,
        )
    assert backend.calls == 0
