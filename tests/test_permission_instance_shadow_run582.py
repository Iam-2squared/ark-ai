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
def test_instance_method_shadow_assignment_is_denied(effect):
    registry, call, grants, token, backend = _case(effect)
    gate = PermissionGate()

    with pytest.raises(AttributeError, match="immutable"):
        gate.authorize = lambda *_args, **_kwargs: None

    accepted = gate.authorize_registered(
        registry, call, grants, now_ms=10,
        one_shot=token if effect is Effect.WRITE else None,
    )
    assert accepted.call is call
    assert gate._consumed_tokens == (
        {"local-token"} if effect is Effect.WRITE else set()
    )
    assert backend.calls == 0


def test_replay_stays_denied_after_instance_shadow_assignment_is_refused():
    registry, call, grants, token, backend = _case(Effect.WRITE)
    gate = PermissionGate()
    gate.authorize_registered(registry, call, grants, now_ms=10, one_shot=token)
    assert gate._consumed_tokens == {"local-token"}

    with pytest.raises(AttributeError, match="immutable"):
        gate.authorize = lambda *_args, **_kwargs: None
    with pytest.raises(PermissionDenied, match="already consumed"):
        gate.authorize_registered(
            registry, call, grants, now_ms=10, one_shot=token,
        )
    assert gate._consumed_tokens == {"local-token"}
    assert backend.calls == 0


def test_grant_iterator_cannot_shadow_gate_method():
    registry, call, grants, token, backend = _case(Effect.WRITE)
    gate = PermissionGate()

    def checked_grants():
        yield grants[0]
        with pytest.raises(AttributeError, match="immutable"):
            gate.authorize = lambda *_args, **_kwargs: None

    accepted = gate.authorize_registered(
        registry, call, checked_grants(), now_ms=10, one_shot=token,
    )
    assert accepted.call is call
    assert gate._consumed_tokens == {"local-token"}
    assert backend.calls == 0


def test_method_shadow_cannot_launder_a_replayed_token():
    registry, call, grants, token, backend = _case(Effect.WRITE)
    gate = PermissionGate()

    with pytest.raises(AttributeError, match="immutable"):
        gate.authorize = lambda *_args, **_kwargs: None
    accepted = gate.authorize_registered(
        registry, call, grants, now_ms=10, one_shot=token,
    )
    assert accepted.call is call
    with pytest.raises(PermissionDenied, match="already consumed"):
        gate.authorize_registered(
            registry, call, grants, now_ms=10, one_shot=token,
        )
    assert backend.calls == 0
