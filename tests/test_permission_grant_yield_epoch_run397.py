"""A yielded grant cannot temporarily rebase the policy before exhaustion.

All cases are inert local PermissionGate checks, not authorization to send
data, execute a ToolBackend, or rely on this process-local token after reboot.
"""

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


@pytest.mark.parametrize(
    "mutation",
    ("prior_grant", "spec_effect", "call_scope", "token_expiry", "token_id"),
)
def test_transient_generator_policy_drift_denied_without_token_spend(mutation):
    call = ToolCall("offline", "fixture-cap", "private-fixture")
    spec = ToolSpec("offline", "fixture-cap", Effect.WRITE)
    first = CapabilityGrant("fixture-cap", "private-fixture", 100)
    second = CapabilityGrant("fixture-cap", "private-fixture", 100)
    token = OneShotAuthorization("fixture-token", call.request_id, 100)
    gate = PermissionGate()
    choices = {
        "prior_grant": (first, "scope", "other"),
        "spec_effect": (spec, "effect", Effect.READ),
        "call_scope": (call, "scope", "other"),
        "token_expiry": (token, "expires_at_ms", 0),
        "token_id": (token, "token_id", "forged-token"),
    }
    target, name, forged = choices[mutation]
    original_value = getattr(target, name)

    def grants():
        yield first
        object.__setattr__(target, name, forged)
        yield second
        object.__setattr__(target, name, original_value)

    with pytest.raises(PermissionDenied, match="changed during grants"):
        gate.authorize(spec, call, grants(), now_ms=10, one_shot=token)
    assert gate._consumed_tokens == set()
    object.__setattr__(target, name, original_value)
    gate.authorize(spec, call, (first, second), now_ms=10, one_shot=token)
    assert gate._consumed_tokens == {"fixture-token"}


@pytest.mark.parametrize("mutation", ("prior_grant", "spec_effect", "call_scope"))
def test_read_diagnostic_also_refuses_transient_grant_drift(mutation):
    call = ToolCall("offline", "fixture-cap", "private-fixture")
    spec = ToolSpec("offline", "fixture-cap", Effect.READ)
    first = CapabilityGrant("fixture-cap", "private-fixture")
    second = CapabilityGrant("fixture-cap", "private-fixture")
    choices = {
        "prior_grant": (first, "scope", "other"),
        "spec_effect": (spec, "effect", Effect.WRITE),
        "call_scope": (call, "scope", "other"),
    }
    target, name, forged = choices[mutation]

    def grants():
        yield first
        object.__setattr__(target, name, forged)
        yield second
        object.__setattr__(target, name, (
            "private-fixture" if name == "scope" else Effect.READ
        ))

    with pytest.raises(PermissionDenied, match="changed during grants"):
        PermissionGate().authorize(spec, call, grants(), now_ms=10)


@pytest.mark.parametrize("effect", (Effect.READ, Effect.WRITE))
def test_unchanged_two_yield_policy_is_still_accepted(effect):
    call = ToolCall("offline", "fixture-cap", "private-fixture")
    spec = ToolSpec("offline", "fixture-cap", effect)
    grant = CapabilityGrant("fixture-cap", "private-fixture")
    token = (
        OneShotAuthorization("fixture-token", call.request_id, 100)
        if effect is Effect.WRITE else None
    )
    gate = PermissionGate()
    gate.authorize(
        spec, call, (item for item in (grant, grant)),
        now_ms=10, one_shot=token,
    )
    assert gate._consumed_tokens == (
        {"fixture-token"} if effect is Effect.WRITE else set()
    )
