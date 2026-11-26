"""A mutable private recheck callback may not spend a stale local WRITE token."""

from types import MappingProxyType

import pytest

from ark.agency import (
    CapabilityGrant,
    Effect,
    OneShotAuthorization,
    PermissionDenied,
    PermissionGate,
    ToolCall,
    ToolSpec,
)


@pytest.mark.parametrize("mutation", (
    "grant_scope", "grant_expiry", "spec_effect", "equal_arguments",
    "token_expiry",
))
def test_reentrant_recheck_mutation_rejected_before_local_token_spend(mutation):
    spec = ToolSpec("fixture.write", "fixture.write", Effect.WRITE)
    call = ToolCall("fixture.write", "fixture.write", "local:test", {"x": 1})
    grant = CapabilityGrant("fixture.write", "local:test", expires_at_ms=200)
    token = OneShotAuthorization("local-" + mutation, call.request_id, 200)
    gate = PermissionGate()

    def injected_recheck():
        if mutation == "grant_scope":
            object.__setattr__(grant, "scope", "local:other")
        elif mutation == "grant_expiry":
            object.__setattr__(grant, "expires_at_ms", 1)
        elif mutation == "spec_effect":
            object.__setattr__(spec, "effect", Effect.READ)
        elif mutation == "equal_arguments":
            object.__setattr__(call, "arguments", MappingProxyType({"x": 1}))
        else:
            object.__setattr__(token, "expires_at_ms", 199)

    with pytest.raises(PermissionDenied, match="changed"):
        gate.authorize(
            spec, call, [grant], now_ms=10, one_shot=token,
            _registered_recheck=injected_recheck,
        )

    # A denied local admission must not consume its token; no backend exists.
    clean_spec = ToolSpec("fixture.write", "fixture.write", Effect.WRITE)
    clean_call = ToolCall("fixture.write", "fixture.write", "local:test", {"x": 1})
    clean_grant = CapabilityGrant("fixture.write", "local:test", expires_at_ms=200)
    clean_token = OneShotAuthorization(
        "local-" + mutation, clean_call.request_id, 200,
    )
    gate.authorize(
        clean_spec, clean_call, [clean_grant], now_ms=10,
        one_shot=clean_token,
    )
    with pytest.raises(PermissionDenied, match="already consumed"):
        gate.authorize(
            clean_spec, clean_call, [clean_grant], now_ms=10,
            one_shot=clean_token,
        )
