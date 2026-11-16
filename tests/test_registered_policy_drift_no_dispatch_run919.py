"""Registered WRITE authorization remains inert and input-epoch bound.

A process-local token spend is not restart-safe approval or authorization to
dispatch a real tool. Synthetic registry backends must not be executed.
"""

from __future__ import annotations

import pytest

from ark.agency.contracts import (
    CapabilityGrant, Effect, OneShotAuthorization, PermissionDenied, ToolCall,
)
from ark.agency.policy import PermissionGate
from ark.agency.registry import ToolRegistration, ToolRegistry


class _NeverExecute:
    def __init__(self):
        self.executions = 0

    def execute(self, _call):
        self.executions += 1
        raise AssertionError("registered policy must not dispatch a tool")


def _fixture():
    backend = _NeverExecute()
    registry = ToolRegistry((
        ToolRegistration(
            "fixture.write", "offline.write", Effect.WRITE,
            "disconnected-only", backend,
        ),
    ))
    call = ToolCall("fixture.write", "offline.write", "sandbox", {"n": 1})
    grant = CapabilityGrant("offline.write", "sandbox")
    token = OneShotAuthorization("synthetic-once", call.request_id, 1000)
    return backend, registry, call, grant, token


@pytest.mark.parametrize("drift", ("grant", "token", "call"))
def test_registered_write_rejects_mid_iterator_identity_drift_before_spend(drift):
    backend, registry, call, grant, token = _fixture()
    gate = PermissionGate()

    def stale_grants():
        yield grant
        if drift == "grant":
            object.__setattr__(grant, "scope", "foreign")
        elif drift == "token":
            object.__setattr__(token, "token_id", "replaced-token")
        else:
            object.__setattr__(call, "scope", "foreign")
        yield grant

    with pytest.raises(PermissionDenied):
        gate.authorize_registered(
            registry, call, stale_grants(), now_ms=100, one_shot=token,
        )
    assert gate._consumed_tokens == set()
    assert backend.executions == 0


def test_registry_write_effect_cannot_be_downgraded_to_read_without_token():
    backend, registry, call, grant, _token = _fixture()
    with pytest.raises(PermissionDenied, match="one-shot"):
        PermissionGate().authorize_registered(
            registry, call, (grant,), now_ms=100,
        )
    assert backend.executions == 0


def test_registered_write_local_token_spend_is_still_not_execution():
    backend, registry, call, grant, token = _fixture()
    gate = PermissionGate()
    bound = gate.authorize_registered(
        registry, call, (grant,), now_ms=100, one_shot=token,
    )
    assert bound.registration.effect is Effect.WRITE
    assert bound.call is call
    assert token.token_id in gate._consumed_tokens
    assert backend.executions == 0
    with pytest.raises(PermissionDenied, match="already consumed"):
        gate.authorize_registered(
            registry, call, (grant,), now_ms=101, one_shot=token,
        )
    assert backend.executions == 0
