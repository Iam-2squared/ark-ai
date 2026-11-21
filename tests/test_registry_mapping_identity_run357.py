"""Exact registry identity-map epoch regressions; no backend dispatch."""

from __future__ import annotations

from types import MappingProxyType

import pytest

from ark.agency.contracts import Effect, ToolCall
from ark.agency.registry import ToolRegistration, ToolRegistry


class _NeverExecute:
    def __init__(self) -> None:
        self.calls = 0

    def execute(self, call: ToolCall) -> object:
        self.calls += 1
        raise AssertionError("registry integrity verification must not execute tools")


def _example() -> tuple[ToolRegistry, ToolCall, _NeverExecute]:
    backend = _NeverExecute()
    registry = ToolRegistry(
        [ToolRegistration("local.read", "files.read", Effect.READ, "mock.read:v1", backend)]
    )
    call = ToolCall("local.read", "files.read", "workspace:synthetic", {"path": "fixture"})
    return registry, call, backend


@pytest.mark.parametrize("carrier", ("new_proxy", "plain_dict"))
@pytest.mark.parametrize("operation", ("revision", "registrations", "get", "resolve", "bind"))
def test_reflected_mapping_replacement_rejected(
    carrier: str, operation: str
) -> None:
    registry, call, backend = _example()
    original = registry.registrations
    replacement = dict(original)
    object.__setattr__(
        registry,
        "_registrations",
        MappingProxyType(replacement) if carrier == "new_proxy" else replacement,
    )
    with pytest.raises(ValueError, match="registry identity map changed"):
        if operation == "revision":
            _ = registry.revision
        elif operation == "registrations":
            _ = registry.registrations
        elif operation == "get":
            registry.get("local.read")
        elif operation == "resolve":
            registry.resolve(call)
        else:
            registry.bind(call)
    assert backend.calls == 0


def test_unmodified_mapping_still_binds_deterministically_without_dispatch() -> None:
    registry, call, backend = _example()
    first = registry.bind(call)
    second = registry.bind(call)
    assert first.bound_action_id == second.bound_action_id
    assert first.registration is registry.registrations["local.read"]
    assert backend.calls == 0
