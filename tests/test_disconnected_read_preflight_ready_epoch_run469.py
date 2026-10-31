"""READ-only plan preflight rejects fabricated or reordered ready-step carriers.

All calls use disconnected mock backends; no external dispatch, credentials,
persistent authorization, or real data.
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
        raise AssertionError("a READ preflight must never execute a backend")


def _inputs(*, independent: bool = False):
    backend = NoDispatchBackend()
    registry = ToolRegistry((
        ToolRegistration("reader", "fixture.read", Effect.READ, "mock", backend),
    ))
    a = PlanStep("a", ToolCall("reader", "fixture.read", "sandbox", {"item": "a"}))
    b = PlanStep(
        "b",
        ToolCall("reader", "fixture.read", "sandbox", {"item": "b"}),
        () if independent else ("a",),
    )
    plan = PlanGraph((b, a))
    return plan, registry, PermissionGate(), (CapabilityGrant("fixture.read", "sandbox"),)


@pytest.mark.parametrize("selection", ("omitted", "descendant", "duplicate", "clone", "list"))
def test_preflight_rejects_fabricated_ready_step_selection(monkeypatch, selection):
    plan, registry, gate, grants = _inputs()
    first, descendant = plan.steps["a"], plan.steps["b"]
    selected = {
        "omitted": (),
        "descendant": (descendant,),
        "duplicate": (first, first),
        "clone": (PlanStep("a", first.call),),
        "list": [first],
    }[selection]
    monkeypatch.setattr(PlanGraph, "ready_steps", lambda self: selected)

    with pytest.raises(DisconnectedReadPreflightRejected, match="ready-step"):
        preview_registered_read_plan(
            plan, registry, gate, grants, observed_at_ms=100,
        )


def test_preflight_rejects_reordered_independent_ready_steps(monkeypatch):
    plan, registry, gate, grants = _inputs(independent=True)
    monkeypatch.setattr(
        PlanGraph, "ready_steps",
        lambda self: (self.steps["b"], self.steps["a"]),
    )
    with pytest.raises(DisconnectedReadPreflightRejected, match="ready-step"):
        preview_registered_read_plan(
            plan, registry, gate, grants, observed_at_ms=100,
        )


def test_preflight_accepts_exact_authoritative_ready_order_without_dispatch():
    plan, registry, gate, grants = _inputs(independent=True)
    preview = preview_registered_read_plan(
        plan, registry, gate, grants, observed_at_ms=100,
    )
    assert preview.ready_step_ids == ("a", "b")
    assert len(preview.ready_bound_ids) == 2
    assert preview.dispatch_authorized is False
    assert preview.external_result_verified is False
