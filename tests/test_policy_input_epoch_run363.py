"""Reentrant grant generators must not redirect local permission authority."""

import pytest

from ark.agency.contracts import (
    CapabilityGrant,
    Effect,
    OneShotAuthorization,
    PermissionDenied,
    ToolCall,
    ToolSpec,
)
from ark.agency.policy import PermissionGate


def _values(effect=Effect.READ):
    call = ToolCall("fixture.tool", "fixture.cap", "scope:one")
    spec = ToolSpec("fixture.tool", "fixture.cap", effect)
    grant = CapabilityGrant("fixture.cap", "scope:one")
    return spec, call, grant


def test_read_scope_mutation_during_grant_iteration_is_denied():
    spec, call, grant = _values()

    def grants():
        yield grant
        object.__setattr__(call, "scope", "scope:two")

    with pytest.raises(PermissionDenied, match="changed during grants"):
        PermissionGate().authorize(spec, call, grants(), now_ms=10)


def test_write_effect_downgrade_during_grants_is_denied_without_token():
    spec, call, grant = _values(Effect.WRITE)

    def grants():
        yield grant
        object.__setattr__(spec, "effect", Effect.READ)

    with pytest.raises(PermissionDenied, match="changed during grants"):
        PermissionGate().authorize(spec, call, grants(), now_ms=10)


def test_matched_grant_mutation_after_yield_cannot_authorize():
    spec, call, grant = _values()

    def grants():
        yield grant
        object.__setattr__(grant, "scope", "scope:other")

    with pytest.raises(PermissionDenied, match="changed during grants"):
        PermissionGate().authorize(spec, call, grants(), now_ms=10)


def test_write_token_mutation_during_grants_cannot_consume_token():
    spec, call, grant = _values(Effect.WRITE)
    token = OneShotAuthorization("synthetic-token", call.request_id, 100)
    gate = PermissionGate()

    def grants():
        yield grant
        object.__setattr__(token, "expires_at_ms", 999)

    with pytest.raises(PermissionDenied, match="changed during grants"):
        gate.authorize(spec, call, grants(), now_ms=10, one_shot=token)
    object.__setattr__(token, "expires_at_ms", 100)
    gate.authorize(spec, call, [grant], now_ms=10, one_shot=token)
    with pytest.raises(PermissionDenied, match="already consumed"):
        gate.authorize(spec, call, [grant], now_ms=10, one_shot=token)


def test_reflected_grant_with_invalid_expiry_is_denied():
    spec, call, grant = _values()
    object.__setattr__(grant, "expires_at_ms", True)
    with pytest.raises(PermissionDenied, match="grant identity is invalid"):
        PermissionGate().authorize(spec, call, [grant], now_ms=10)


def test_unchanged_exact_scoped_grants_retain_read_and_write_behavior():
    spec, call, grant = _values()
    PermissionGate().authorize(spec, call, iter((grant,)), now_ms=10)
    write_spec = ToolSpec(spec.name, spec.capability, Effect.WRITE)
    token = OneShotAuthorization("synthetic-token", call.request_id, 100)
    PermissionGate().authorize(
        write_spec, call, iter((grant,)), now_ms=10, one_shot=token
    )
