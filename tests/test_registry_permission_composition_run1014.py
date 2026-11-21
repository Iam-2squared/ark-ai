"""Run1014: compose exact ToolRegistry binding with exact PermissionGate policy.

The test authorizes a synthetic WRITE request locally but never dispatches the
registered backend. The one-shot token is process-local and is not durable
approval or evidence of an external effect.
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


class _NeverExecute:
    def __init__(self) -> None:
        self.calls = 0

    def execute(self, call: ToolCall) -> object:
        self.calls += 1
        raise AssertionError("authorization composition must not dispatch")


def test_registered_write_binds_exact_registry_and_spends_local_token_once() -> None:
    backend = _NeverExecute()
    registration = ToolRegistration(
        "fixture.write",
        "fixture.write",
        Effect.WRITE,
        "disconnected.mock.v1",
        backend,
    )
    registry = ToolRegistry((registration,))
    call = ToolCall(
        "fixture.write",
        "fixture.write",
        "synthetic:scope",
        {"value": "synthetic-only"},
    )
    original_binding = registry.bind(call)
    gate = PermissionGate()
    grants = (CapabilityGrant("fixture.write", "synthetic:scope"),)
    token = OneShotAuthorization("synthetic-token", call.request_id, 500)

    authorized = gate.authorize_registered(
        registry,
        call,
        grants,
        now_ms=100,
        one_shot=token,
    )

    assert authorized.registry_revision == original_binding.registry_revision
    assert authorized.registry_revision == registry.revision
    assert authorized.bound_action_id == original_binding.bound_action_id
    assert authorized.registration is registration
    assert authorized.call.request_id == call.request_id
    assert backend.calls == 0

    with pytest.raises(PermissionDenied, match="already consumed"):
        gate.authorize_registered(
            registry,
            call,
            grants,
            now_ms=100,
            one_shot=token,
        )
    assert backend.calls == 0
