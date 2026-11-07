"""An inert READ cycle must not invoke substituted authority descriptors.

A read-only mock result is NOT dispatch consent, verified external execution
or a durable replay capability. Test backends are explicitly unreachable.
"""

import pytest

import ark.agency.disconnected_read_cycle as cycle
from ark.agency.contracts import CapabilityGrant, Effect, PlanStep, StepState, ToolCall
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
        raise AssertionError("an inert READ cycle cannot call the backend")


def _inputs():
    backend = NeverExecute()
    registry = ToolRegistry((
        ToolRegistration("reader", "fixture.read", Effect.READ, "mock", backend),
    ))
    plan = PlanGraph((
        PlanStep("a", ToolCall("reader", "fixture.read", "private")),
        PlanStep("b", ToolCall("reader", "fixture.read", "private"), ("a",)),
    ))
    grants = (CapabilityGrant("fixture.read", "private", expires_at_ms=500),)
    return plan, registry, PermissionGate(), grants, backend


def _run(inputs):
    plan, registry, gate, grants, _ = inputs
    return cycle.simulate_registered_read_cycle(
        plan, registry, gate, grants, observed_at_ms=100,
    )


@pytest.mark.parametrize("flag", _FLAGS)
@pytest.mark.parametrize("moment", ("entry", "after_preflight"))
def test_false_looking_descriptor_replacement_cannot_be_invoked(
    monkeypatch, flag, moment,
):
    inputs = _inputs()
    plan, _, gate, _, backend = inputs
    initial_status = plan.status_digest()
    getter_calls = []

    def fake_denial(self):
        getter_calls.append(flag)
        return False

    def substitute():
        monkeypatch.setattr(
            cycle.DisconnectedReadCycleReceipt, flag, property(fake_denial),
        )

    if moment == "entry":
        substitute()
    else:
        original_preview = cycle.preview_registered_read_plan

        def preview_and_replace(*args, **kwargs):
            receipt = original_preview(*args, **kwargs)
            substitute()
            return receipt

        monkeypatch.setattr(cycle, "preview_registered_read_plan", preview_and_replace)

    with pytest.raises(
        cycle.DisconnectedReadCycleRejected,
        match="simulation receipt changed: denial descriptor substituted",
    ):
        _run(inputs)
    assert getter_calls == []
    assert backend.calls == 0
    assert not gate._consumed_tokens
    assert plan.status_digest() == initial_status
    assert all(s.state is StepState.PENDING for s in plan.statuses().values())


def test_original_result_denials_allow_only_inert_shadow_progress():
    inputs = _inputs()
    receipt = _run(inputs)
    assert len(receipt.wave_bound_step_hashes) == 2
    for field in _FLAGS:
        assert getattr(receipt, field) is False
    assert inputs[-1].calls == 0
    assert not inputs[2]._consumed_tokens
    assert all(s.state is StepState.PENDING for s in inputs[0].statuses().values())
