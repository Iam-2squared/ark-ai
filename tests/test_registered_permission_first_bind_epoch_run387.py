"""First registry callback cannot redefine the authorized action or token.

Synthetic diagnostics only: an authorized receipt never dispatches the backend.
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


class NeverExecute:
    def execute(self, call: ToolCall) -> object:
        raise AssertionError("permission diagnostics must never dispatch")


def _inputs(effect=Effect.WRITE):
    registry = ToolRegistry((
        ToolRegistration("mock", "cap", effect, "local", NeverExecute()),
    ))
    call = ToolCall("mock", "cap", "fixture", {"n": 1})
    token = OneShotAuthorization("original-token", call.request_id, 1_000)
    grants = (CapabilityGrant("cap", "fixture"),)
    return registry, call, token, grants


@pytest.mark.parametrize("field,replacement", [
    ("scope", "other-scope"),
    ("arguments", {"n": 2}),
])
@pytest.mark.parametrize("during_bind", [1, 2])
def test_registered_action_epoch_precedes_registry_callbacks(
    monkeypatch, field, replacement, during_bind,
):
    registry, call, token, grants = _inputs()
    gate = PermissionGate()
    original = getattr(call, field)
    bind = registry.bind
    counter = 0

    def redirect(current):
        nonlocal counter
        counter += 1
        if counter == during_bind:
            object.__setattr__(call, field, replacement)
        return bind(current)

    monkeypatch.setattr(registry, "bind", redirect)
    with pytest.raises(PermissionDenied, match="identity"):
        gate.authorize_registered(
            registry, call, grants, now_ms=10, one_shot=token,
        )
    assert gate._consumed_tokens == set()
    object.__setattr__(call, field, original)
    monkeypatch.setattr(registry, "bind", bind)
    gate.authorize_registered(registry, call, grants, now_ms=10, one_shot=token)


@pytest.mark.parametrize("field,replacement", [
    ("token_id", "substituted-token"),
    ("request_id", "act_" + "f" * 64),
    ("expires_at_ms", 2_000),
])
@pytest.mark.parametrize("during_bind", [1, 2])
def test_registered_token_epoch_precedes_registry_callbacks(
    monkeypatch, field, replacement, during_bind,
):
    registry, call, token, grants = _inputs()
    gate = PermissionGate()
    original = getattr(token, field)
    bind = registry.bind
    counter = 0

    def redirect(current):
        nonlocal counter
        counter += 1
        if counter == during_bind:
            object.__setattr__(token, field, replacement)
        return bind(current)

    monkeypatch.setattr(registry, "bind", redirect)
    with pytest.raises(PermissionDenied, match="identity"):
        gate.authorize_registered(
            registry, call, grants, now_ms=10, one_shot=token,
        )
    assert gate._consumed_tokens == set()
    object.__setattr__(token, field, original)
    monkeypatch.setattr(registry, "bind", bind)
    gate.authorize_registered(registry, call, grants, now_ms=10, one_shot=token)


def test_first_registry_bind_epoch_is_enforced_for_read_only():
    registry, call, _token, grants = _inputs(Effect.READ)
    bind = registry.bind

    def mutate_before_bind(current):
        object.__setattr__(call, "scope", "another-scope")
        return bind(current)

    registry.bind = mutate_before_bind
    with pytest.raises(PermissionDenied, match="identity"):
        PermissionGate().authorize_registered(registry, call, grants, now_ms=10)


def test_unchanged_registered_read_and_write_require_no_backend():
    for effect in (Effect.READ, Effect.WRITE):
        registry, call, token, grants = _inputs(effect)
        result = PermissionGate().authorize_registered(
            registry, call, grants, now_ms=10,
            one_shot=token if effect is Effect.WRITE else None,
        )
        assert result.call is call
        assert result.registration.effect is effect
