"""Registry-bound grant iteration must reject transient identity rebasing.

No backend is dispatched. One-shot tokens are process-local mock diagnostics,
not human approval, durable authorization, or external WRITE evidence.
"""

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


class NeverDispatch:
    def execute(self, call):
        raise AssertionError("registered policy must not execute a backend")


def _fixture(effect=Effect.WRITE):
    registration = ToolRegistration(
        "offline", "fixture-cap", effect, "mock-backend", NeverDispatch(),
    )
    registry = ToolRegistry((registration,))
    call = ToolCall("offline", "fixture-cap", "private-fixture")
    token = OneShotAuthorization("fixture-token", call.request_id, 100)
    first = CapabilityGrant("fixture-cap", "private-fixture", 100)
    second = CapabilityGrant("fixture-cap", "private-fixture", 100)
    return registry, registration, call, token, first, second


@pytest.mark.parametrize(
    ("mutation", "diagnostic"),
    (
        ("previous_grant", "registered grant identity changed"),
        ("registration_effect", "registry binding changed"),
        ("call_scope", "registered input identity changed"),
        ("token_id", "registered input identity changed"),
        ("token_expiry", "registered input identity changed"),
    ),
)
def test_registered_grant_generator_intermediate_drift_denied_before_spend(
    mutation, diagnostic,
):
    registry, registration, call, token, first, second = _fixture()
    gate = PermissionGate()
    options = {
        "previous_grant": (first, "scope", "different"),
        "registration_effect": (registration, "effect", Effect.READ),
        "call_scope": (call, "scope", "different"),
        "token_id": (token, "token_id", "different"),
        "token_expiry": (token, "expires_at_ms", 0),
    }
    target, field, changed = options[mutation]
    original = getattr(target, field)

    def grants():
        yield first
        object.__setattr__(target, field, changed)
        yield second
        object.__setattr__(target, field, original)

    with pytest.raises(PermissionDenied, match=diagnostic):
        gate.authorize_registered(
            registry, call, grants(), now_ms=10, one_shot=token,
        )
    assert gate._consumed_tokens == set()
    object.__setattr__(target, field, original)
    allowed = gate.authorize_registered(
        registry, call, (first, second), now_ms=10, one_shot=token,
    )
    assert allowed.registration.effect is Effect.WRITE
    assert gate._consumed_tokens == {"fixture-token"}


@pytest.mark.parametrize("effect", (Effect.READ, Effect.WRITE))
def test_registered_unchanged_generator_remains_inert_and_valid(effect):
    registry, _registration, call, token, first, second = _fixture(effect)
    gate = PermissionGate()
    result = gate.authorize_registered(
        registry, call, (x for x in (first, second)),
        now_ms=10, one_shot=token if effect is Effect.WRITE else None,
    )
    assert result.registration.effect is effect
    assert gate._consumed_tokens == (
        {"fixture-token"} if effect is Effect.WRITE else set()
    )
