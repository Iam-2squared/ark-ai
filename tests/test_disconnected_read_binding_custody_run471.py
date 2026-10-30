"""Frozen bound READ carriers remain pinned across reentrant permission checks.

All requests use synthetic READ-only registry entries with a backend that must
never be called. Preflight is a diagnostic, not real dispatch authorization.
"""

from __future__ import annotations

import pytest

from ark.agency.contracts import CapabilityGrant, Effect, PlanStep, ToolCall
from ark.agency.disconnected_read_preflight import (
    DisconnectedReadPreflightRejected,
    preview_registered_read_plan,
)
from ark.agency.planner import PlanGraph
from ark.agency.policy import PermissionGate
from ark.agency.registry import ToolRegistration, ToolRegistry


class NoDispatchBackend:
    def execute(self, call: ToolCall) -> object:
        raise AssertionError("disconnected READ preflight dispatched a backend")


def _setup():
    backend = NoDispatchBackend()
    registry = ToolRegistry((
        ToolRegistration("reader", "fixture.read", Effect.READ, "mock", backend),
    ))
    steps = tuple(
        PlanStep(name, ToolCall("reader", "fixture.read", "sandbox", {"item": name}))
        for name in ("a", "b")
    )
    return (
        PlanGraph(steps), registry, PermissionGate(),
        (CapabilityGrant("fixture.read", "sandbox"),),
    )


def _alter_bound(bound, mode: str) -> None:
    if mode == "id":
        initial = bound.bound_action_id
        replacement = (" " + initial)[1:]
        assert replacement == initial and replacement is not initial
        object.__setattr__(bound, "bound_action_id", replacement)
    elif mode == "revision":
        initial = bound.registry_revision
        replacement = (" " + initial)[1:]
        assert replacement == initial and replacement is not initial
        object.__setattr__(bound, "registry_revision", replacement)
    elif mode == "registration":
        old = bound.registration
        replacement = ToolRegistration(
            old.name, old.capability, old.effect, old.backend_id, old.backend,
        )
        assert replacement == old and replacement is not old
        object.__setattr__(bound, "registration", replacement)
    elif mode == "call":
        old = bound.call
        replacement = ToolCall(old.tool, old.capability, old.scope, dict(old.arguments))
        assert replacement == old and replacement is not old
        object.__setattr__(bound, "call", replacement)
    else:
        raise AssertionError("invalid test mode")


@pytest.mark.parametrize("mode", ("id", "revision", "registration", "call"))
@pytest.mark.parametrize("tamper_on_gate_number", (1, 2))
def test_gate_cannot_replace_any_earlier_bound_carrier(
    monkeypatch, mode, tamper_on_gate_number,
):
    plan, registry, gate, grants = _setup()
    original_bind = ToolRegistry.bind
    original_authorize = PermissionGate.authorize_registered
    first_bound = []
    calls = []

    def capture_bind(self, call):
        result = original_bind(self, call)
        if call is plan.steps["a"].call and not first_bound:
            first_bound.append(result)
        return result

    def adversarial_gate(self, registry, call, grants, *, now_ms, one_shot=None):
        result = original_authorize(
            self, registry, call, grants, now_ms=now_ms, one_shot=one_shot,
        )
        calls.append(call)
        if len(calls) == tamper_on_gate_number:
            _alter_bound(first_bound[0], mode)
        return result

    monkeypatch.setattr(ToolRegistry, "bind", capture_bind)
    monkeypatch.setattr(PermissionGate, "authorize_registered", adversarial_gate)
    with pytest.raises(DisconnectedReadPreflightRejected, match="binding carrier"):
        preview_registered_read_plan(
            plan, registry, gate, grants, observed_at_ms=100,
        )
    assert len(calls) == tamper_on_gate_number


def test_unchanged_independent_reads_pass_without_dispatch():
    plan, registry, gate, grants = _setup()
    preview = preview_registered_read_plan(
        plan, registry, gate, grants, observed_at_ms=100,
    )
    assert preview.ready_step_ids == ("a", "b")
    assert len(preview.ready_bound_ids) == 2
    assert preview.dispatch_authorized is False
    assert preview.external_result_verified is False
    assert preview.authenticated_clock_or_consent is False
