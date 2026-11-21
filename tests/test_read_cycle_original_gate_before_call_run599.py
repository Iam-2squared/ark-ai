"""Independent READ-wave gate must be original before direct use.

These cases deliberately forge local PermissionGate methods after a valid
preflight. Neither a returned mock receipt nor a READ grant can dispatch a
backend, prove consent, or license replay.
"""

import pytest

import ark.agency.disconnected_read_cycle as cycle
from ark.agency.contracts import CapabilityGrant, Effect, PlanStep, StepState, ToolCall
from ark.agency.planner import PlanGraph
from ark.agency.policy import PermissionGate
from ark.agency.registry import ToolRegistration, ToolRegistry


class NeverDispatch:
    def __init__(self):
        self.calls = 0

    def execute(self, call):
        self.calls += 1
        raise AssertionError("READ preview cannot invoke a backend")


def _inputs():
    backend = NeverDispatch()
    registry = ToolRegistry((
        ToolRegistration("fixture.read", "local.read", Effect.READ, "mock", backend),
    ))
    plan = PlanGraph((
        PlanStep("a", ToolCall("fixture.read", "local.read", "private", {"n": 1})),
        PlanStep("b", ToolCall("fixture.read", "local.read", "private"), ("a",)),
    ))
    gate = PermissionGate()
    grants = (CapabilityGrant("local.read", "private", expires_at_ms=500),)
    return plan, registry, gate, grants, backend


@pytest.mark.parametrize("location", ("class", "instance"))
@pytest.mark.parametrize("moment", ("after_preview", "during_rebind"))
def test_spoofed_gate_is_never_invoked_by_independent_wave(
    monkeypatch, location, moment,
):
    plan, registry, gate, grants, backend = _inputs()
    original_preview = cycle.preview_registered_read_plan
    counter = []

    def counterfeit(self, registry, call, grants, *, now_ms, one_shot=None):
        counter.append(call.tool)
        return registry.bind(call)

    def install_spoof():
        if location == "class":
            monkeypatch.setattr(PermissionGate, "authorize_registered", counterfeit)
        else:
            monkeypatch.setattr(
                gate, "authorize_registered",
                lambda registry, call, grants, *, now_ms, one_shot=None: counterfeit(
                    gate, registry, call, grants,
                    now_ms=now_ms, one_shot=one_shot,
                ),
            )

    def preview_then_change(*args, **kwargs):
        receipt = original_preview(*args, **kwargs)
        if moment == "after_preview":
            install_spoof()
        else:
            original_bind = registry.bind

            def changed_bind(call):
                result = original_bind(call)
                install_spoof()
                return result

            monkeypatch.setattr(registry, "bind", changed_bind)
        return receipt

    monkeypatch.setattr(cycle, "preview_registered_read_plan", preview_then_change)
    with pytest.raises(
        cycle.DisconnectedReadCycleRejected,
        match="READ wave registered gate implementation changed",
    ):
        cycle.simulate_registered_read_cycle(
            plan, registry, gate, grants, observed_at_ms=100,
        )
    assert counter == []
    assert backend.calls == 0
    assert gate._consumed_tokens == set()
    assert all(state.state is StepState.PENDING for state in plan.statuses().values())


def test_original_gate_still_advances_two_inert_shadow_waves():
    plan, registry, gate, grants, backend = _inputs()
    original_status = plan.status_digest()
    receipt = cycle.simulate_registered_read_cycle(
        plan, registry, gate, grants, observed_at_ms=100,
    )
    assert len(receipt.wave_bound_step_hashes) == 2
    assert receipt.dispatch_authorized is False
    assert receipt.external_result_verified is False
    assert receipt.automatic_replay_authorized is False
    assert receipt.authenticated_clock_or_consent is False
    assert plan.status_digest() == original_status
    assert backend.calls == 0
    assert gate._consumed_tokens == set()
