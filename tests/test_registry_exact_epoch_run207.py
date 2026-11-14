"""Reflected epoch carrier regressions; checks never dispatch a tool."""

from __future__ import annotations

import pytest

from ark.agency.contracts import Effect, ToolCall
from ark.agency.registry import ToolRegistration, ToolRegistry


class _EqualText(str):
    """Value-equal but non-exact string that must never carry registry identity."""


class _NeverDispatch:
    def __init__(self) -> None:
        self.calls = 0

    def execute(self, call: ToolCall) -> object:
        self.calls += 1
        raise AssertionError("registry inspection must never dispatch")


def _registry() -> tuple[ToolRegistry, ToolRegistration, ToolCall, _NeverDispatch]:
    backend = _NeverDispatch()
    registration = ToolRegistration(
        "files.read", "files.read", Effect.READ, "mock.files.read:v1", backend
    )
    registry = ToolRegistry([registration])
    call = ToolCall("files.read", "files.read", "workspace:fixture", {"path": "x"})
    return registry, registration, call, backend


@pytest.mark.parametrize("field", ("name", "capability", "backend_id"))
@pytest.mark.parametrize("method", ("revision", "registrations", "get", "resolve", "bind"))
def test_value_equal_subclass_in_registered_identity_fails_closed(
    field: str, method: str
) -> None:
    registry, registration, call, backend = _registry()
    object.__setattr__(registration, field, _EqualText(getattr(registration, field)))
    with pytest.raises(ValueError, match="registered tool identity drifted"):
        if method == "revision":
            _ = registry.revision
        elif method == "registrations":
            _ = registry.registrations
        elif method == "get":
            registry.get("files.read")
        elif method == "resolve":
            registry.resolve(call)
        else:
            registry.bind(call)
    assert backend.calls == 0


@pytest.mark.parametrize("method", ("revision", "registrations", "get", "resolve", "bind"))
def test_value_equal_subclass_in_revision_fails_closed(method: str) -> None:
    registry, _, call, backend = _registry()
    object.__setattr__(registry, "_revision", _EqualText(registry.revision))
    with pytest.raises(ValueError, match=r"registry revision carrier (?:was )?changed"):
        if method == "revision":
            _ = registry.revision
        elif method == "registrations":
            _ = registry.registrations
        elif method == "get":
            registry.get("files.read")
        elif method == "resolve":
            registry.resolve(call)
        else:
            registry.bind(call)
    assert backend.calls == 0


def test_exact_unchanged_epoch_preserves_deterministic_identity() -> None:
    registry, registration, call, backend = _registry()
    first, second = registry.bind(call), registry.bind(call)
    assert first.bound_action_id == second.bound_action_id
    assert first.registry_revision == second.registry_revision == registry.revision
    assert first.registration is second.registration is registration
    assert backend.calls == 0
