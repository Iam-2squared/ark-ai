"""Second/under-lock registry rebinds cannot rewrite retained grant epochs.

Disconnected and synthetic only: no backend execution, authenticated consent, or
durable cross-process one-shot guarantee is established here.
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
        raise AssertionError("the policy review must not execute any backend")


@pytest.mark.parametrize("effect", (Effect.READ, Effect.WRITE))
@pytest.mark.parametrize("bind_phase", (2, 3))
@pytest.mark.parametrize(
    ("field", "replacement"),
    (
        ("capability", "retargeted-capability"),
        ("scope", "retargeted-scope"),
        ("expires_at_ms", 0),
        ("expires_at_ms", object()),
    ),
)
def test_registered_rebind_grant_epoch_change_fails_before_any_write_spend(
    monkeypatch, effect, bind_phase, field, replacement,
):
    registration = ToolRegistration(
        "fixture-tool", "fixture-capability", effect,
        "fixture-backend", NeverDispatch(),
    )
    registry = ToolRegistry((registration,))
    call = ToolCall("fixture-tool", "fixture-capability", "fixture-scope")
    token = OneShotAuthorization("synthetic-token", call.request_id, 100)
    original_grant = CapabilityGrant("fixture-capability", "fixture-scope", 100)
    later_grant = CapabilityGrant("fixture-capability", "fixture-scope", 100)
    gate = PermissionGate()
    real_bind = registry.bind
    calls = 0
    original = getattr(original_grant, field)

    def reflected_bind(current_call):
        nonlocal calls
        calls += 1
        result = real_bind(current_call)
        if calls == bind_phase:
            # Mutation after the originally valid registry binding, before
            # returning control to registered policy's next checkpoint.
            object.__setattr__(original_grant, field, replacement)
        return result

    monkeypatch.setattr(registry, "bind", reflected_bind)
    with pytest.raises(PermissionDenied, match="registered grant identity changed"):
        gate.authorize_registered(
            registry, call, (original_grant, later_grant), now_ms=10,
            one_shot=token if effect is Effect.WRITE else None,
        )
    assert gate._consumed_tokens == set()
    assert calls == bind_phase

    # Fail-closed rejection must not consume even the synthetic token. A
    # separate, unchanged attempt remains possible, without dispatching tools.
    object.__setattr__(original_grant, field, original)
    monkeypatch.setattr(registry, "bind", real_bind)
    permitted = gate.authorize_registered(
        registry, call, (original_grant, later_grant), now_ms=10,
        one_shot=token if effect is Effect.WRITE else None,
    )
    assert permitted.registration is registration
    assert gate._consumed_tokens == (
        {"synthetic-token"} if effect is Effect.WRITE else set()
    )
