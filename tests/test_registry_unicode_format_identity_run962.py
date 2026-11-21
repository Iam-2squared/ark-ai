"""Run962: opt-in registry refuses Unicode bidirectional and line-format spoofing.

The frozen generic ToolCall/Grant contracts are unchanged. Mock backends never
execute; process-local token tests provide no real action authorization.
"""

from __future__ import annotations

import pytest

from ark.agency.contracts import (
    CapabilityGrant,
    Effect,
    OneShotAuthorization,
    PermissionDenied,
    ToolCall,
)
from ark.agency.policy import PermissionGate
from ark.agency.registry import ToolRegistration, ToolRegistry

_FORMAT_CONTROLS = (
    "\u0085", "\u061c", "\u200e", "\u200f",
    "\u2028", "\u2029", "\u202a", "\u202b", "\u202c",
    "\u202d", "\u202e", "\u2066", "\u2067", "\u2068", "\u2069",
)


class NoDispatch:
    def __init__(self) -> None:
        self.calls = 0

    def execute(self, call: ToolCall) -> object:
        self.calls += 1
        raise AssertionError("format-control admission must never execute a backend")


@pytest.mark.parametrize("control", _FORMAT_CONTROLS)
@pytest.mark.parametrize("field", ("name", "capability", "backend_id"))
def test_registration_rejects_format_spoof_before_binding(
    control: str, field: str,
) -> None:
    backend = NoDispatch()
    labels = {
        "name": "fixture.read",
        "capability": "offline.read",
        "backend_id": "disconnected",
    }
    labels[field] += control + "forged"
    with pytest.raises(ValueError, match="Unicode formatting control"):
        ToolRegistration(
            labels["name"], labels["capability"], Effect.READ,
            labels["backend_id"], backend,
        )
    assert backend.calls == 0


@pytest.mark.parametrize("control", _FORMAT_CONTROLS)
@pytest.mark.parametrize("operation", ("resolve", "bind"))
def test_registry_bound_scope_rejects_format_spoof(
    control: str, operation: str,
) -> None:
    backend = NoDispatch()
    registry = ToolRegistry((
        ToolRegistration("fixture.read", "offline.read", Effect.READ, "mock", backend),
    ))
    call = ToolCall("fixture.read", "offline.read", "local" + control + "scope")
    with pytest.raises(ValueError, match="Unicode formatting control"):
        getattr(registry, operation)(call)
    assert backend.calls == 0


@pytest.mark.parametrize("control", ("\u202e", "\u2067", "\u2028"))
def test_bad_scope_does_not_consume_unrelated_one_shot(control: str) -> None:
    backend = NoDispatch()
    registry = ToolRegistry((
        ToolRegistration("fixture.write", "offline.write", Effect.WRITE, "mock", backend),
    ))
    good = ToolCall("fixture.write", "offline.write", "private")
    bad = ToolCall("fixture.write", "offline.write", "private" + control + "other")
    grant = CapabilityGrant("offline.write", "private", expires_at_ms=1000)
    token = OneShotAuthorization("synthetic-token", good.request_id, 1000)
    gate = PermissionGate()
    with pytest.raises(PermissionDenied, match="registry binding"):
        gate.authorize_registered(
            registry, bad, (grant,), now_ms=100, one_shot=token,
        )
    allowed = gate.authorize_registered(
        registry, good, (grant,), now_ms=100, one_shot=token,
    )
    assert allowed.call is good
    with pytest.raises(PermissionDenied):
        gate.authorize_registered(
            registry, good, (grant,), now_ms=100, one_shot=token,
        )
    assert backend.calls == 0


def test_unicode_letters_remain_distinct_and_resolvable_without_execution() -> None:
    backend = NoDispatch()
    registration = ToolRegistration(
        "fixture.שלום", "offline.温度", Effect.READ, "local-β", backend,
    )
    registry = ToolRegistry((registration,))
    call = ToolCall("fixture.שלום", "offline.温度", "خصوصية/東京")
    assert registry.resolve(call) is registration
    assert registry.bind(call).bound_action_id.startswith("bound_")
    assert backend.calls == 0
