"""Bound caller-provided grant generators before any synthetic token spend.

This is an in-process permission diagnostic; no backend is invoked and no
real human approval or durable authorization is established.
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
from ark.agency.policy import _MAX_GRANTS, PermissionGate
from ark.agency.registry import ToolRegistration, ToolRegistry


class NeverExecute:
    def execute(self, call: ToolCall) -> object:
        raise AssertionError("a grant budget check must never dispatch")


@pytest.mark.parametrize("registered", (False, True))
@pytest.mark.parametrize("effect", (Effect.READ, Effect.WRITE))
def test_oversize_grant_generator_denied_without_token_spend(registered, effect):
    call = ToolCall("offline", "fixture-cap", "private-scope")
    spec = ToolSpec("offline", "fixture-cap", effect)
    registry = ToolRegistry((
        ToolRegistration("offline", "fixture-cap", effect, "mock", NeverExecute()),
    ))
    grant = CapabilityGrant("fixture-cap", "private-scope")
    token = (
        OneShotAuthorization("reusable", call.request_id, 100)
        if effect is Effect.WRITE else None
    )
    gate = PermissionGate()
    advances = 0

    def infinite_like():
        nonlocal advances
        for _ in range(_MAX_GRANTS + 20):
            advances += 1
            yield grant

    with pytest.raises(PermissionDenied, match="grant budget exceeded"):
        if registered:
            gate.authorize_registered(
                registry, call, infinite_like(), now_ms=10, one_shot=token,
            )
        else:
            gate.authorize(
                spec, call, infinite_like(), now_ms=10, one_shot=token,
            )
    assert advances == _MAX_GRANTS + 1
    assert gate._consumed_tokens == set()

    # A denied over-budget iterator cannot burn the original WRITE token.
    if registered:
        gate.authorize_registered(registry, call, [grant], now_ms=10, one_shot=token)
    else:
        gate.authorize(spec, call, [grant], now_ms=10, one_shot=token)
    assert gate._consumed_tokens == (
        {"reusable"} if effect is Effect.WRITE else set()
    )


@pytest.mark.parametrize("registered", (False, True))
def test_exact_budget_is_accepted_with_no_backend_dispatch(registered):
    call = ToolCall("offline", "fixture-cap", "private-scope")
    spec = ToolSpec("offline", "fixture-cap", Effect.READ)
    registry = ToolRegistry((
        ToolRegistration(
            "offline", "fixture-cap", Effect.READ, "mock", NeverExecute(),
        ),
    ))
    grant = CapabilityGrant("fixture-cap", "private-scope")
    grants = (grant for _ in range(_MAX_GRANTS))
    gate = PermissionGate()
    if registered:
        result = gate.authorize_registered(registry, call, grants, now_ms=10)
        assert result.call is call
    else:
        gate.authorize(spec, call, grants, now_ms=10)
    assert gate._consumed_tokens == set()
