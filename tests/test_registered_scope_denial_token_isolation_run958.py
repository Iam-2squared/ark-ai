"""Run958: invalid registry scope cannot consume a one-shot WRITE token.

This is a process-local, disconnected policy check. It is NOT durable
authorization, external exactly-once execution, or authenticated consent.
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


class _NoDispatch:
    def __init__(self) -> None:
        self.calls = 0

    def execute(self, call: ToolCall) -> object:
        self.calls += 1
        raise AssertionError("identity and permission review cannot dispatch")


@pytest.mark.parametrize(
    "invalid_scope",
    ("local:private\x00other", "local:private\ud800", "界" * 86),
)
def test_invalid_registered_write_identity_never_spends_unrelated_valid_token(
    invalid_scope: str,
) -> None:
    backend = _NoDispatch()
    registry = ToolRegistry((
        ToolRegistration(
            "offline.write", "offline.capability", Effect.WRITE,
            "disconnected:mock", backend,
        ),
    ))
    gate = PermissionGate()
    valid = ToolCall("offline.write", "offline.capability", "local:private")
    invalid = ToolCall("offline.write", "offline.capability", invalid_scope)
    grant = CapabilityGrant("offline.capability", "local:private", 200)
    token = OneShotAuthorization("fixture-once", valid.request_id, 200)

    with pytest.raises(PermissionDenied):
        gate.authorize_registered(
            registry, invalid, (grant,), now_ms=100, one_shot=token,
        )
    assert gate._consumed_tokens == set()
    assert backend.calls == 0

    # A correctly bound call can still consume the original local token
    # once; an unsuccessful invalid-scope attempt cannot poison it.
    bound = gate.authorize_registered(
        registry, valid, (grant,), now_ms=100, one_shot=token,
    )
    assert bound.call is valid
    assert bound.registration.effect is Effect.WRITE
    assert gate._consumed_tokens == {"fixture-once"}
    with pytest.raises(PermissionDenied, match="already consumed"):
        gate.authorize_registered(
            registry, valid, (grant,), now_ms=100, one_shot=token,
        )
    assert backend.calls == 0
