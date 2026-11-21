"""Run960: opt-in registry identities and scopes reject control delimiters.

The frozen generic ToolCall/Grant contracts remain unchanged.  All backends
are inert mocks; token checks are process-local and confer no real authority.
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

_CONTROLS = ("\n", "\r", "\t", "\x01", "\x1f", "\x7f")


class InertBackend:
    def __init__(self) -> None:
        self.calls = 0

    def execute(self, call: ToolCall) -> object:
        self.calls += 1
        raise AssertionError("registry admission must never execute a backend")


@pytest.mark.parametrize("control", _CONTROLS)
@pytest.mark.parametrize("field", ("name", "capability", "backend_id"))
def test_registration_rejects_control_character_before_backend_binding(
    control: str, field: str,
) -> None:
    backend = InertBackend()
    fields = {
        "name": "fixture.read", "capability": "offline.read",
        "backend_id": "inert-fixture",
    }
    fields[field] += control + "suffix"
    with pytest.raises(ValueError, match="control character"):
        ToolRegistration(
            fields["name"], fields["capability"], Effect.READ,
            fields["backend_id"], backend,
        )
    assert backend.calls == 0


@pytest.mark.parametrize("control", _CONTROLS)
@pytest.mark.parametrize("method", ("resolve", "bind"))
def test_opt_in_resolution_refuses_control_scope_before_action_identity(
    control: str, method: str,
) -> None:
    backend = InertBackend()
    registry = ToolRegistry((
        ToolRegistration("fixture.read", "offline.read", Effect.READ, "mock", backend),
    ))
    call = ToolCall("fixture.read", "offline.read", "private" + control + "other")
    with pytest.raises(ValueError, match="control character"):
        getattr(registry, method)(call)
    assert backend.calls == 0


@pytest.mark.parametrize("control", _CONTROLS)
def test_bad_registered_write_scope_cannot_consume_unrelated_one_shot(
    control: str,
) -> None:
    backend = InertBackend()
    registry = ToolRegistry((
        ToolRegistration("fixture.write", "offline.write", Effect.WRITE, "mock", backend),
    ))
    good = ToolCall("fixture.write", "offline.write", "private")
    bad = ToolCall("fixture.write", "offline.write", "private" + control + "other")
    grant = CapabilityGrant("offline.write", "private", expires_at_ms=1000)
    token = OneShotAuthorization("fixture-token", good.request_id, 1000)
    gate = PermissionGate()
    with pytest.raises(PermissionDenied, match="registry binding"):
        gate.authorize_registered(
            registry, bad, (grant,), now_ms=100, one_shot=token,
        )
    bound = gate.authorize_registered(
        registry, good, (grant,), now_ms=100, one_shot=token,
    )
    assert bound.call is good
    assert bound.registration.effect is Effect.WRITE
    with pytest.raises(PermissionDenied):
        gate.authorize_registered(
            registry, good, (grant,), now_ms=100, one_shot=token,
        )
    assert backend.calls == 0


def test_valid_unicode_identifiers_remain_resolvable_without_execution() -> None:
    backend = InertBackend()
    registration = ToolRegistration(
        "fixture.測定", "offline.温度", Effect.READ, "local-β", backend,
    )
    registry = ToolRegistry((registration,))
    call = ToolCall("fixture.測定", "offline.温度", "private/測定")
    assert registry.resolve(call) is registration
    bound = registry.bind(call)
    assert bound.call is call
    assert bound.registration is registration
    assert bound.bound_action_id.startswith("bound_")
    assert backend.calls == 0
