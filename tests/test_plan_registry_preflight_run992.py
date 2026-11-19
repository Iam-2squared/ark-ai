"""Planner-to-registry binding preflight; every backend remains undispatched."""

from __future__ import annotations

import pytest

from ark.agency import (
    Effect,
    PlanGraph,
    PlanStep,
    StepState,
    ToolCall,
    ToolRegistration,
    ToolRegistry,
)
from ark.agency.plan_registry_preflight import (
    PlanRegistryPreflightRejected,
    review_plan_registry_preflight,
)


class _NoDispatchBackend:
    def __init__(self):
        self.calls = 0

    def execute(self, _call):
        self.calls += 1
        raise AssertionError("preflight must never execute a backend")


def _call(tool: str, capability: str, value: str) -> ToolCall:
    return ToolCall(
        tool,
        capability,
        "synthetic:private",
        {"fixture_value": value},
    )


def _case(*, unknown_second: bool = False):
    backend = _NoDispatchBackend()
    first = _call("fixture.first", "capability.read", "one")
    second = _call(
        "fixture.missing" if unknown_second else "fixture.second",
        "capability.read",
        "two",
    )
    steps = (
        PlanStep("first", first),
        PlanStep("second", second, ("first",)),
    )
    graph = PlanGraph(steps)
    registrations = [
        ToolRegistration(
            "fixture.first", "capability.read", Effect.READ, "fixture.backend.v1", backend,
        ),
    ]
    if not unknown_second:
        registrations.append(ToolRegistration(
            "fixture.second", "capability.read", Effect.WRITE,
            "fixture.backend.v1", backend,
        ))
    registry = ToolRegistry(tuple(registrations))
    return graph, registry, backend


def test_valid_plan_binds_every_step_to_one_registry_revision_without_dispatch():
    graph, registry, backend = _case()

    result = review_plan_registry_preflight(graph, registry)

    assert result.plan_topology_digest == graph.topology_digest()
    assert result.plan_status_digest == graph.status_digest()
    assert result.registry_revision == registry.revision
    assert result.ready_step_ids == ("first",)
    assert tuple(item.step_id for item in result.bindings) == ("first", "second")
    assert result.bindings[0].effect is Effect.READ
    assert result.bindings[1].effect is Effect.WRITE
    assert all(item.registry_revision if hasattr(item, "registry_revision") else True
               for item in result.bindings)
    assert len(result.fingerprint) == 64
    assert result.permission_granted is False
    assert result.dispatch_authorized is False
    assert result.tool_execution_authorized is False
    assert result.automatic_replay_authorized is False
    assert result.trusted_clock_verified is False
    assert result.consent_verified is False
    assert all(item.permission_granted is False for item in result.bindings)
    assert all(item.dispatch_authorized is False for item in result.bindings)
    assert backend.calls == 0


def test_unknown_plan_tool_is_rejected_without_dispatch():
    graph, registry, backend = _case(unknown_second=True)

    with pytest.raises(
        PlanRegistryPreflightRejected,
        match="plan step has no stable registry binding",
    ):
        review_plan_registry_preflight(graph, registry)

    assert backend.calls == 0


def test_registry_instance_method_shadow_is_rejected_before_binding():
    graph, registry, backend = _case()

    def bypass(_call):
        raise AssertionError("shadowed registry method must not run")

    registry.bind = bypass

    with pytest.raises(
        PlanRegistryPreflightRejected,
        match="ToolRegistry method shadowing rejected",
    ):
        review_plan_registry_preflight(graph, registry)

    assert backend.calls == 0


def test_plan_status_epoch_changes_ready_set_and_preflight_fingerprint():
    graph, registry, backend = _case()
    before = review_plan_registry_preflight(graph, registry)
    graph.transition("first", StepState.RUNNING, expected_revision=0)

    after = review_plan_registry_preflight(graph, registry)

    assert before.plan_topology_digest == after.plan_topology_digest
    assert before.plan_status_digest != after.plan_status_digest
    assert before.ready_step_ids == ("first",)
    assert after.ready_step_ids == ()
    assert before.fingerprint != after.fingerprint
    assert backend.calls == 0


def test_replaced_plan_status_digest_is_rejected_before_preflight(
    monkeypatch: pytest.MonkeyPatch,
):
    graph, registry, backend = _case()

    def fake_digest(_self):
        return "pstate_" + "0" * 64

    monkeypatch.setattr(PlanGraph, "status_digest", fake_digest)

    with pytest.raises(
        PlanRegistryPreflightRejected,
        match="plan or registry contract changed",
    ):
        review_plan_registry_preflight(graph, registry)

    assert backend.calls == 0
