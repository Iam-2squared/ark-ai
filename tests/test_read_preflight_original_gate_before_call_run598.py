"""Original gate identity must be checked before a spoof can run.

These fixtures never execute a backend. A fake PermissionGate method must be
rejected *before invocation*, even if it returns a value-equal BoundAction.
"""

import pytest

from ark.agency.contracts import CapabilityGrant, Effect, PlanStep, ToolCall
from ark.agency.disconnected_read_preflight import (
    DisconnectedReadPreflightRejected,
    preview_registered_read_plan,
)
from ark.agency.planner import PlanGraph
from ark.agency.policy import PermissionGate
from ark.agency.registry import ToolRegistration, ToolRegistry


class NoDispatch:
    calls = 0

    def execute(self, call):
        self.calls += 1
        raise AssertionError("no real tool dispatch is authorized")


def _fixture():
    backend = NoDispatch()
    registry = ToolRegistry((
        ToolRegistration("local.read", "local.read", Effect.READ, "mock", backend),
    ))
    plan = PlanGraph((
        PlanStep("read", ToolCall("local.read", "local.read", "private", {"n": 1})),
    ))
    gate = PermissionGate()
    grants = (CapabilityGrant("local.read", "private", expires_at_ms=100),)
    return plan, registry, gate, grants, backend


def _preview(items):
    plan, registry, gate, grants, _ = items
    return preview_registered_read_plan(
        plan, registry, gate, grants, observed_at_ms=5,
    )


def _install_spy(monkeypatch, gate, hits):
    def forged(self, registry, call, grants, *, now_ms, one_shot=None):
        hits.append(call.tool)
        return registry.bind(call)

    monkeypatch.setattr(PermissionGate, "authorize_registered", forged)


def test_preinstalled_class_fake_gate_is_never_invoked(monkeypatch):
    items = _fixture()
    hits = []
    _install_spy(monkeypatch, items[2], hits)
    with pytest.raises(
        DisconnectedReadPreflightRejected,
        match="registered READ gate implementation changed",
    ):
        _preview(items)
    assert hits == []
    assert items[-1].calls == 0
    assert items[2]._consumed_tokens == set()


def test_registry_bind_callback_cannot_invoke_new_class_fake_gate(monkeypatch):
    items = _fixture()
    _plan, registry, gate, _grants, backend = items
    original_bind = registry.bind
    hits = []

    def substituted_bind(call):
        bound = original_bind(call)
        _install_spy(monkeypatch, gate, hits)
        return bound

    monkeypatch.setattr(registry, "bind", substituted_bind)
    with pytest.raises(
        DisconnectedReadPreflightRejected,
        match="registered READ gate implementation changed",
    ):
        _preview(items)
    assert hits == []
    assert backend.calls == 0
    assert gate._consumed_tokens == set()


def test_unmodified_gate_still_previews_without_dispatch():
    items = _fixture()
    receipt = _preview(items)
    assert receipt.ready_step_ids == ("read",)
    assert receipt.dispatch_authorized is False
    assert receipt.authenticated_clock_or_consent is False
    assert items[-1].calls == 0


def test_instance_gate_method_shadow_is_rejected_before_read_preflight():
    items = _fixture()
    gate = items[2]
    with pytest.raises(AttributeError, match="immutable"):
        gate.authorize_registered = lambda *_args, **_kwargs: None

    receipt = _preview(items)
    assert receipt.ready_step_ids == ("read",)
    assert receipt.dispatch_authorized is False
    assert items[-1].calls == 0
    assert gate._consumed_tokens == set()


def test_registry_callback_cannot_shadow_instance_gate_method():
    items = _fixture()
    _plan, registry, gate, _grants, backend = items
    original_bind = registry.bind

    def substituted_bind(call):
        with pytest.raises(AttributeError, match="immutable"):
            gate.authorize_registered = lambda *_args, **_kwargs: None
        return original_bind(call)

    monkeypatch = pytest.MonkeyPatch()
    try:
        monkeypatch.setattr(registry, "bind", substituted_bind)
        receipt = _preview(items)
    finally:
        monkeypatch.undo()
    assert receipt.ready_step_ids == ("read",)
    assert receipt.dispatch_authorized is False
    assert backend.calls == 0
