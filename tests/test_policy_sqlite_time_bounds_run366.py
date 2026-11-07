"""Synthetic authorization time contracts are safe for future durable storage."""

import pytest

from ark.agency import (
    CapabilityGrant,
    Effect,
    OneShotAuthorization,
    PermissionGate,
    ToolCall,
    ToolSpec,
)

MAX = (1 << 63) - 1


@pytest.mark.parametrize("invalid", (-1, True, MAX + 1, 1 << 100))
def test_capability_grant_refuses_out_of_range_expiry(invalid):
    with pytest.raises(ValueError, match="expires_at_ms"):
        CapabilityGrant("fixture.write", "fixture:scope", expires_at_ms=invalid)


@pytest.mark.parametrize("invalid", (-1, True, MAX + 1, 1 << 100))
def test_one_shot_refuses_out_of_range_expiry(invalid):
    with pytest.raises(ValueError, match="expires_at_ms"):
        OneShotAuthorization("fixture-token", "act_" + "0" * 64, invalid)


@pytest.mark.parametrize("invalid", (-1, True, MAX + 1, 1 << 100))
def test_invalid_now_never_consumes_authorization_token(invalid):
    gate = PermissionGate()
    call = ToolCall("fixture.write", "fixture.write", "fixture:scope")
    spec = ToolSpec(call.tool, call.capability, Effect.WRITE)
    grant = CapabilityGrant(call.capability, call.scope, expires_at_ms=MAX)
    token = OneShotAuthorization("fixture-token", call.request_id, MAX)
    with pytest.raises(ValueError, match="now_ms"):
        gate.authorize(spec, call, [grant], now_ms=invalid, one_shot=token)
    gate.authorize(spec, call, [grant], now_ms=MAX - 1, one_shot=token)


def test_exact_maximum_expiry_is_accepted_but_exclusive():
    call = ToolCall("fixture.read", "fixture.read", "fixture:scope")
    spec = ToolSpec(call.tool, call.capability, Effect.READ)
    grant = CapabilityGrant(call.capability, call.scope, expires_at_ms=MAX)
    PermissionGate().authorize(spec, call, [grant], now_ms=MAX - 1)
    from ark.agency import PermissionDenied

    with pytest.raises(PermissionDenied, match="no active"):
        PermissionGate().authorize(spec, call, [grant], now_ms=MAX)
