"""Synthetic registry-bound scope budget and mutable-carrier regressions.

The v1 ToolCall constructor is unchanged. A bound identity does not authorize
backend dispatch or grant process-external exactly-once effects.
"""

from __future__ import annotations

import pytest

import ark.agency.registry as registry_module
from ark.agency import Effect, ToolCall, ToolRegistration, ToolRegistry


class InertBackend:
    def execute(self, _call):
        pytest.fail("registry-only tests must never execute a backend")


def _registry():
    return ToolRegistry((
        ToolRegistration("fixture", "read", Effect.READ, "mock", InertBackend()),
    ))


@pytest.mark.parametrize(
    "bad_scope",
    (
        "s" * 4097,
        "界" * 1366,
        "a" * 262144,
    ),
    ids=("codepoint", "utf8-bytes", "reflected-oversize"),
)
def test_resolve_and_bind_reject_oversized_scope_before_request_hash(bad_scope):
    registry = _registry()
    call = ToolCall("fixture", "read", "safe")
    # Simulate an otherwise-valid frozen ToolCall reflected after construction.
    object.__setattr__(call, "scope", bad_scope)
    with pytest.raises(ValueError, match="scope exceeds registry budget"):
        registry.resolve(call)
    with pytest.raises(ValueError, match="scope exceeds registry budget"):
        registry.bind(call)


def test_registry_accepts_exact_unicode_boundary_without_backend_dispatch():
    registry = _registry()
    call = ToolCall("fixture", "read", "界" * 1365)
    bound = registry.bind(call)
    assert bound.call is call
    assert bound.registration is registry.resolve(call)
    assert bound.registry_revision == registry.revision
    assert bound.bound_action_id.startswith("bound_")


def test_replaced_registry_scope_admission_is_not_trusted(monkeypatch):
    registry = _registry()
    call = ToolCall("fixture", "read", "safe")
    with monkeypatch.context() as patch:
        patch.setattr(registry_module, "_registry_scope_budget", lambda _value: None)
        with pytest.raises(ValueError, match="scope admission changed"):
            registry.resolve(call)
        with pytest.raises(ValueError, match="scope admission changed"):
            registry.bind(call)
