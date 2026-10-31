"""Registry/Planner/Gate integration remains disconnected and READ-only."""

from __future__ import annotations

import pytest

from ark.agency.contracts import (
    CapabilityGrant,
    Effect,
    PlanStep,
    StepState,
    ToolCall,
)
from ark.agency.disconnected_read_preflight import (
    DisconnectedReadPreflightRejected,
    preview_registered_read_plan,
)
from ark.agency.planner import PlanGraph
from ark.agency.policy import PermissionGate
from ark.agency.registry import ToolRegistration, ToolRegistry


class ExplosiveBackend:
    def __init__(self) -> None:
        self.calls = 0

    def execute(self, call: ToolCall) -> object:
        self.calls += 1
        raise AssertionError("preflight must NEVER dispatch a backend")


def setup_read_plan(*, effect: Effect = Effect.READ):
    backend = ExplosiveBackend()
    registry = ToolRegistry((
        ToolRegistration("fixture.reader", "fixture.read", effect, "mock-v1", backend),
    ))
    first = PlanStep(
        "a", ToolCall("fixture.reader", "fixture.read", "sandbox", {"secret": "canary"})
    )
    second = PlanStep(
        "b", ToolCall("fixture.reader", "fixture.read", "sandbox", {"item": 2}), ("a",)
    )
    graph = PlanGraph((first, second))
    grant = CapabilityGrant("fixture.read", "sandbox", expires_at_ms=200)
    return graph, registry, PermissionGate(), grant, backend


def test_ready_read_is_content_free_and_never_executes_backend():
    graph, registry, gate, grant, backend = setup_read_plan()
    output = preview_registered_read_plan(
        graph, registry, gate, (grant,), observed_at_ms=100,
    )
    assert output.ready_step_ids == ("a",)
    assert len(output.ready_bound_ids) == 1
    assert len(output.fingerprint) == 64
    assert output.dispatch_authorized is False
    assert output.external_result_verified is False
    assert output.authenticated_clock_or_consent is False
    assert output.automatic_replay_authorized is False
    assert "canary" not in repr(output)
    assert backend.calls == 0
    repeated = preview_registered_read_plan(
        graph, registry, gate, (grant,), observed_at_ms=100,
    )
    assert output == repeated
    assert backend.calls == 0


def test_ready_steps_advance_after_success_but_never_execute():
    graph, registry, gate, grant, backend = setup_read_plan()
    first = preview_registered_read_plan(
        graph, registry, gate, (grant,), observed_at_ms=100,
    )
    graph.transition("a", StepState.RUNNING, expected_revision=0)
    graph.transition("a", StepState.SUCCEEDED, expected_revision=1)
    second = preview_registered_read_plan(
        graph, registry, gate, (grant,), observed_at_ms=100,
    )
    assert second.ready_step_ids == ("b",)
    assert second.fingerprint != first.fingerprint
    assert backend.calls == 0


def test_clock_observation_changes_digest_not_permissions():
    graph, registry, gate, grant, backend = setup_read_plan()
    a = preview_registered_read_plan(
        graph, registry, gate, (grant,), observed_at_ms=98,
    )
    b = preview_registered_read_plan(
        graph, registry, gate, (grant,), observed_at_ms=99,
    )
    assert a.fingerprint != b.fingerprint
    assert a.authenticated_clock_or_consent is False
    assert backend.calls == 0


@pytest.mark.parametrize("clock", (200, 201, 2**63 - 1))
def test_expired_read_grant_denied_without_dispatch(clock: int):
    graph, registry, gate, grant, backend = setup_read_plan()
    with pytest.raises(DisconnectedReadPreflightRejected, match="grant"):
        preview_registered_read_plan(
            graph, registry, gate, (grant,), observed_at_ms=clock,
        )
    assert backend.calls == 0


def test_wrong_scope_denied_without_dispatch():
    graph, registry, gate, _, backend = setup_read_plan()
    with pytest.raises(DisconnectedReadPreflightRejected, match="grant"):
        preview_registered_read_plan(
            graph, registry, gate,
            (CapabilityGrant("fixture.read", "other"),), observed_at_ms=100,
        )
    assert backend.calls == 0


def test_registered_write_denied_even_if_only_descendant_is_write():
    graph, registry, gate, grant, backend = setup_read_plan(effect=Effect.WRITE)
    with pytest.raises(DisconnectedReadPreflightRejected, match="non-READ"):
        preview_registered_read_plan(
            graph, registry, gate, (grant,), observed_at_ms=100,
        )
    assert backend.calls == 0


def test_unknown_tool_is_denied_without_execution():
    graph, _, gate, grant, _ = setup_read_plan()
    backend = ExplosiveBackend()
    other = ToolRegistry((
        ToolRegistration("different.reader", "fixture.read", Effect.READ, "v1", backend),
    ))
    with pytest.raises(DisconnectedReadPreflightRejected, match="unregistered"):
        preview_registered_read_plan(graph, other, gate, (grant,), observed_at_ms=100)
    assert backend.calls == 0


def test_cancelled_root_has_no_ready_steps_or_authority():
    graph, registry, gate, grant, backend = setup_read_plan()
    graph.transition("a", StepState.CANCELLED, expected_revision=0)
    output = preview_registered_read_plan(
        graph, registry, gate, (grant,), observed_at_ms=100,
    )
    assert output.ready_step_ids == ()
    assert output.ready_bound_ids == ()
    assert output.dispatch_authorized is False
    assert backend.calls == 0


@pytest.mark.parametrize("bad", ([], None, (object(),), tuple(range(129))))
def test_rejects_invalid_grant_carriers(bad):
    graph, registry, gate, _, backend = setup_read_plan()
    with pytest.raises(DisconnectedReadPreflightRejected):
        preview_registered_read_plan(graph, registry, gate, bad, observed_at_ms=100)
    assert backend.calls == 0


@pytest.mark.parametrize("clock", (True, -1, 2**63, "1"))
def test_rejects_untrusted_clock_shape(clock):
    graph, registry, gate, grant, backend = setup_read_plan()
    with pytest.raises(DisconnectedReadPreflightRejected, match="clock"):
        preview_registered_read_plan(graph, registry, gate, (grant,), observed_at_ms=clock)
    assert backend.calls == 0


def test_reentrant_gate_changes_plan_status_and_blocks_result(monkeypatch):
    graph, registry, gate, grant, backend = setup_read_plan()
    original = PermissionGate.authorize_registered

    def mutating_gate(self, registry, call, grants, *, now_ms, one_shot=None):
        bound = original(self, registry, call, grants, now_ms=now_ms, one_shot=one_shot)
        graph.transition("a", StepState.RUNNING, expected_revision=0)
        return bound

    monkeypatch.setattr(PermissionGate, "authorize_registered", mutating_gate)
    with pytest.raises(DisconnectedReadPreflightRejected, match="changed"):
        preview_registered_read_plan(graph, registry, gate, (grant,), observed_at_ms=100)
    assert backend.calls == 0


def test_reentrant_gate_replaces_equal_grant_carrier_and_blocks(monkeypatch):
    graph, registry, gate, grant, backend = setup_read_plan()
    original = PermissionGate.authorize_registered

    def mutating_gate(self, registry, call, grants, *, now_ms, one_shot=None):
        bound = original(self, registry, call, grants, now_ms=now_ms, one_shot=one_shot)
        new_scope = bytes(grant.scope, "utf-8").decode("utf-8")
        assert new_scope == grant.scope and new_scope is not grant.scope
        object.__setattr__(grant, "scope", new_scope)
        return bound

    monkeypatch.setattr(PermissionGate, "authorize_registered", mutating_gate)
    with pytest.raises(DisconnectedReadPreflightRejected, match="grant carrier"):
        preview_registered_read_plan(graph, registry, gate, (grant,), observed_at_ms=100)
    assert backend.calls == 0


def test_reentrant_binding_changes_plan_and_blocks_result(monkeypatch):
    graph, registry, gate, grant, backend = setup_read_plan()
    original = ToolRegistry.bind

    def mutating_bind(self, call):
        bound = original(self, call)
        graph.transition("a", StepState.RUNNING, expected_revision=0)
        return bound

    monkeypatch.setattr(ToolRegistry, "bind", mutating_bind)
    with pytest.raises(DisconnectedReadPreflightRejected, match="changed"):
        preview_registered_read_plan(graph, registry, gate, (grant,), observed_at_ms=100)
    assert backend.calls == 0
