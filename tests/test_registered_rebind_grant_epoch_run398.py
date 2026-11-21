"""Grant epochs remain bound across supported grant-iterator callbacks.

Registry method shadows are denied before invocation; these cases exercise
separate caller-controlled grant iteration boundaries.
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
@pytest.mark.parametrize("grant_phase", (2, 3))
@pytest.mark.parametrize(
    ("field", "replacement"),
    (
        ("capability", "retargeted-capability"),
        ("scope", "retargeted-scope"),
        ("expires_at_ms", 0),
        ("expires_at_ms", object()),
    ),
)
def test_registered_grant_epoch_change_fails_before_any_write_spend(
    effect, grant_phase, field, replacement,
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
    final_grant = CapabilityGrant("fixture-capability", "fixture-scope", 100)
    gate = PermissionGate()
    original = getattr(original_grant, field)

    def stream():
        yield original_grant
        if grant_phase == 2:
            object.__setattr__(original_grant, field, replacement)
        yield later_grant
        if grant_phase == 3:
            object.__setattr__(original_grant, field, replacement)
        yield final_grant

    with pytest.raises(PermissionDenied, match="registered grant identity changed"):
        gate.authorize_registered(
            registry, call, stream(), now_ms=10,
            one_shot=token if effect is Effect.WRITE else None,
        )
    assert gate._consumed_tokens == set()

    # A failed pre-spend grant epoch must not consume the synthetic token.
    object.__setattr__(original_grant, field, original)
    permitted = gate.authorize_registered(
        registry, call, (original_grant, later_grant, final_grant), now_ms=10,
        one_shot=token if effect is Effect.WRITE else None,
    )
    assert permitted.registration is registration
    assert gate._consumed_tokens == (
        {"synthetic-token"} if effect is Effect.WRITE else set()
    )
