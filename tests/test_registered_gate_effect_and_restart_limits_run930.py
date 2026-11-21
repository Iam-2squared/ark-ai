"""Registry effect identity and process-local PermissionGate limits.

Synthetic backends intentionally raise if dispatched. A local one-shot gate
cannot attest approval, preserve a spend across restart, or authorize WRITE.
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


class _InertBackend:
    def __init__(self) -> None:
        self.calls = 0

    def execute(self, call: ToolCall) -> object:
        self.calls += 1
        raise AssertionError("no fixture may execute a tool")


def _registry(effect: Effect, backend: _InertBackend) -> ToolRegistry:
    return ToolRegistry(
        (ToolRegistration("fixture.action", "fixture.cap", effect, "mock-v1", backend),)
    )


def _call() -> ToolCall:
    return ToolCall("fixture.action", "fixture.cap", "private:test", {"value": 1})


def test_same_request_but_registered_write_cannot_inherit_read_authority() -> None:
    backend = _InertBackend()
    call = _call()
    read = _registry(Effect.READ, backend)
    write = _registry(Effect.WRITE, backend)
    grant = CapabilityGrant("fixture.cap", "private:test", expires_at_ms=100)
    gate = PermissionGate()
    assert read.revision != write.revision
    assert read.bind(call).bound_action_id != write.bind(call).bound_action_id
    approved_read = gate.authorize_registered(read, call, [grant], now_ms=50)
    assert approved_read.registration.effect is Effect.READ
    with pytest.raises(PermissionDenied, match="one-shot"):
        gate.authorize_registered(write, call, [grant], now_ms=50)
    assert backend.calls == 0


@pytest.mark.parametrize(
    ("grant_scope", "grant_expiry", "now"),
    (
        ("private:other", 100, 50),
        ("private:test", 50, 50),
        ("private:test", 49, 50),
    ),
)
def test_registry_bound_read_denies_wrong_scope_or_expired_grant(
    grant_scope: str, grant_expiry: int, now: int,
) -> None:
    backend = _InertBackend()
    call = _call()
    registry = _registry(Effect.READ, backend)
    gate = PermissionGate()
    grant = CapabilityGrant("fixture.cap", grant_scope, expires_at_ms=grant_expiry)
    with pytest.raises(PermissionDenied, match="grant"):
        gate.authorize_registered(registry, call, (grant,), now_ms=now)
    assert backend.calls == 0


def test_local_token_spend_is_not_restart_safe_and_never_executes_backend() -> None:
    backend = _InertBackend()
    registry = _registry(Effect.WRITE, backend)
    call = _call()
    grant = CapabilityGrant("fixture.cap", "private:test")
    token = OneShotAuthorization("synthetic-token", call.request_id, 100)
    gate = PermissionGate()
    verified = gate.authorize_registered(
        registry, call, (grant,), now_ms=50, one_shot=token,
    )
    assert verified.registration.effect is Effect.WRITE
    with pytest.raises(PermissionDenied, match="consumed"):
        gate.authorize_registered(
            registry, call, (grant,), now_ms=51, one_shot=token,
        )
    # A new gate has no record of the first spend: this is the deliberately
    # documented limitation, NOT authorization for a real or restarted WRITE.
    new_gate = PermissionGate()
    again = new_gate.authorize_registered(
        registry, call, (grant,), now_ms=52, one_shot=token,
    )
    assert again.bound_action_id == verified.bound_action_id
    assert backend.calls == 0
