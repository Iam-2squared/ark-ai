"""Registered permission must never accept a shadowed instance-level policy.

All tests are synthetic; no backend method executes and no durable grant,
real-world authorization or independent exactly-once proof is created.
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


class _NeverExecute:
    def __init__(self):
        self.calls = 0

    def execute(self, call):
        self.calls += 1
        raise AssertionError("disconnected backend must not execute")


def _case(effect):
    backend = _NeverExecute()
    registry = ToolRegistry((
        ToolRegistration("mock", "cap", effect, "offline", backend),
    ))
    call = ToolCall("mock", "cap", "fixture", {"value": 1})
    grant = CapabilityGrant("cap", "fixture")
    token = OneShotAuthorization("local-token", call.request_id, 100)
    return registry, call, (grant,), token, backend


@pytest.mark.parametrize("effect", (Effect.READ, Effect.WRITE))
def test_fresh_instance_noop_policy_cannot_authorize_registered_action(effect):
    registry, call, grants, token, backend = _case(effect)
    gate = PermissionGate()
    gate.authorize = lambda *_args, **_kwargs: None
    # Both READ and WRITE reject the instance shadow before even a
    # synthetic registry authorization result is returned. No token spends.
    with pytest.raises(PermissionDenied, match="implementation identity changed"):
        gate.authorize_registered(
            registry, call, grants, now_ms=10,
            one_shot=token if effect is Effect.WRITE else None,
        )
    assert gate._consumed_tokens == set()
    assert backend.calls == 0


def test_replay_not_laundered_through_already_consumed_token_and_noop():
    registry, call, grants, token, backend = _case(Effect.WRITE)
    gate = PermissionGate()
    gate.authorize_registered(registry, call, grants, now_ms=10, one_shot=token)
    assert gate._consumed_tokens == {"local-token"}
    gate.authorize = lambda *_args, **_kwargs: None
    with pytest.raises(PermissionDenied, match="implementation identity"):
        gate.authorize_registered(
            registry, call, grants, now_ms=10, one_shot=token,
        )
    assert gate._consumed_tokens == {"local-token"}
    assert backend.calls == 0


def test_policy_shadow_installed_by_grant_iterator_is_rejected_before_spend():
    registry, call, grants, token, backend = _case(Effect.WRITE)
    gate = PermissionGate()

    def redirecting_grants():
        yield grants[0]
        gate.authorize = lambda *_args, **_kwargs: None

    with pytest.raises(PermissionDenied, match="implementation identity changed"):
        gate.authorize_registered(
            registry, call, redirecting_grants(), now_ms=10,
            one_shot=token,
        )
    assert gate._consumed_tokens == set()
    assert backend.calls == 0


def test_removing_instance_shadow_restores_original_policy_not_replay():
    registry, call, grants, token, backend = _case(Effect.WRITE)
    gate = PermissionGate()
    gate.authorize = lambda *_args, **_kwargs: None
    with pytest.raises(PermissionDenied, match="implementation identity changed"):
        gate.authorize_registered(
            registry, call, grants, now_ms=10, one_shot=token,
        )
    del gate.authorize
    accepted = gate.authorize_registered(
        registry, call, grants, now_ms=10, one_shot=token,
    )
    assert accepted.call is call
    with pytest.raises(PermissionDenied, match="already consumed"):
        gate.authorize_registered(
            registry, call, grants, now_ms=10, one_shot=token,
        )
    assert backend.calls == 0
