"""Exact original grant-carrier custody in local-only PermissionGate checks.

Reflected mutable frozen grants can gain equal-valued replacement strings.
No real issuer, durable approval or backend execution is established here.
"""

from threading import Lock

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
from ark.agency.registry import ToolRegistration, ToolRegistry


class NeverExecute:
    def execute(self, call):
        raise AssertionError("a synthetic grant check must not dispatch")


def _fixture(effect=Effect.WRITE):
    call = ToolCall("fixture", "write", "offline")
    spec = ToolSpec("fixture", "write", effect)
    registry = ToolRegistry((
        ToolRegistration("fixture", "write", effect, "mock", NeverExecute()),
    ))
    grant = CapabilityGrant("write", "offline", 100)
    token = OneShotAuthorization("one-shot", call.request_id, 100)
    return PermissionGate(), registry, spec, call, grant, token


def _clone(value):
    result = ("!" + value)[1:]
    assert result == value and result is not value
    return result


@pytest.mark.parametrize("registered", (False, True))
@pytest.mark.parametrize("effect", (Effect.READ, Effect.WRITE))
def test_yielding_second_grant_cannot_hide_equal_carrier_rebinding(
    registered, effect,
):
    gate, registry, spec, call, grant, token = _fixture(effect)
    next_grant = CapabilityGrant("write", "offline", 100)

    def grants():
        yield grant
        object.__setattr__(grant, "capability", _clone(grant.capability))
        yield next_grant

    with pytest.raises(PermissionDenied, match="grant|authorization input changed"):
        if registered:
            gate.authorize_registered(
                registry, call, grants(), now_ms=10,
                one_shot=token if effect is Effect.WRITE else None,
            )
        else:
            gate.authorize(
                spec, call, grants(), now_ms=10,
                one_shot=token if effect is Effect.WRITE else None,
            )
    assert gate._consumed_tokens == set()


@pytest.mark.parametrize("effect", (Effect.READ, Effect.WRITE))
def test_registered_second_binding_cannot_swap_equal_grant_carrier(
    monkeypatch, effect,
):
    gate, registry, _spec, call, grant, token = _fixture(effect)
    bind = registry.bind
    calls = []

    def rebound(current):
        result = bind(current)
        calls.append(True)
        if len(calls) == 2:
            object.__setattr__(grant, "scope", _clone(grant.scope))
        return result

    monkeypatch.setattr(registry, "bind", rebound)
    with pytest.raises(PermissionDenied, match="registered grant identity changed"):
        gate.authorize_registered(
            registry, call, (grant,), now_ms=10,
            one_shot=token if effect is Effect.WRITE else None,
        )
    assert len(calls) == 2
    assert gate._consumed_tokens == set()


def test_equal_carrier_replacement_while_waiting_for_spend_lock_does_not_spend():
    gate, _registry, spec, call, grant, token = _fixture()

    class ReflectedLock:
        def __enter__(self):
            object.__setattr__(grant, "scope", _clone(grant.scope))
            return self

        def __exit__(self, exc_type, exc, tb):
            return False

    gate._token_lock = ReflectedLock()
    with pytest.raises(PermissionDenied, match="during token spend"):
        gate.authorize(spec, call, (grant,), now_ms=10, one_shot=token)
    assert gate._consumed_tokens == set()
    object.__setattr__(grant, "scope", "offline")
    gate._token_lock = Lock()
    gate.authorize(spec, call, (grant,), now_ms=10, one_shot=token)
    assert gate._consumed_tokens == {"one-shot"}


def test_equal_carrier_swap_after_local_spend_never_returns_registered_binding(
    monkeypatch,
):
    gate, registry, _spec, call, grant, token = _fixture()
    original = gate.authorize

    def changed(*args, **kwargs):
        result = original(*args, **kwargs)
        object.__setattr__(grant, "scope", _clone(grant.scope))
        return result

    monkeypatch.setattr(gate, "authorize", changed)
    with pytest.raises(PermissionDenied, match="registered grant identity changed"):
        gate.authorize_registered(
            registry, call, (grant,), now_ms=10, one_shot=token,
        )
    # A process-local token already spent before a post-spend denial remains
    # consumed. No failed action is retried automatically.
    assert gate._consumed_tokens == {"one-shot"}


def test_unchanged_local_registered_write_still_spends_exactly_once():
    gate, registry, _spec, call, grant, token = _fixture()
    bound = gate.authorize_registered(
        registry, call, (grant,), now_ms=10, one_shot=token,
    )
    assert bound.call is call
    assert gate._consumed_tokens == {"one-shot"}
    with pytest.raises(PermissionDenied, match="already consumed"):
        gate.authorize_registered(
            registry, call, (grant,), now_ms=10, one_shot=token,
        )
