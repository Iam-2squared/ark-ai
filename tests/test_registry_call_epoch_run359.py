"""Reject reflected ToolCall mutation during Registry binding without dispatch."""

import pytest

from ark.agency.contracts import Effect, ToolCall
from ark.agency.registry import ToolRegistration, ToolRegistry


class _NeverExecute:
    calls = 0

    def execute(self, call: ToolCall) -> object:
        self.calls += 1
        raise AssertionError("binding must never dispatch")


@pytest.mark.parametrize(
    ("field", "replacement"),
    [
        ("tool", "other.tool"),
        ("capability", "other.capability"),
        ("scope", "workspace:other"),
        ("arguments", {"synthetic": "changed"}),
    ],
)
def test_registry_bind_rejects_drift_during_revision_check(
    field: str, replacement: object
) -> None:
    backend = _NeverExecute()
    registration = ToolRegistration(
        "synthetic.read", "synthetic.read", Effect.READ, "mock:v1", backend
    )
    registry = ToolRegistry((registration,))
    call = ToolCall("synthetic.read", "synthetic.read", "workspace:synthetic", {"x": 1})
    original_compute = registry._compute_revision

    def injected_compute(entries):
        object.__setattr__(call, field, replacement)
        return original_compute(entries)

    registry._compute_revision = injected_compute
    with pytest.raises(ValueError):
        registry.bind(call)
    assert backend.calls == 0


def test_registry_bind_baseline_keeps_revision_and_never_dispatches() -> None:
    backend = _NeverExecute()
    registration = ToolRegistration(
        "synthetic.read", "synthetic.read", Effect.READ, "mock:v1", backend
    )
    registry = ToolRegistry((registration,))
    call = ToolCall("synthetic.read", "synthetic.read", "workspace:synthetic", {"x": 1})
    first = registry.bind(call)
    second = registry.bind(call)
    assert first.bound_action_id == second.bound_action_id
    assert first.registry_revision == registry.revision
    assert first.call is call
    assert backend.calls == 0
