"""Registered action/token identity is rechecked across grant callbacks.

Registry method shadows are denied before invocation; supported grant iterators
remain explicit reentrant boundaries. No backend is dispatched.
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
@pytest.mark.parametrize("mutation_phase", [1, 2])
def test_registered_action_epoch_precedes_grant_iterator_callbacks(
    field, replacement, mutation_phase,
):
    registry, call, token, grants = _inputs()
    gate = PermissionGate()
    original = getattr(call, field)
    grant = grants[0]

    def stream():
        if mutation_phase == 1:
            object.__setattr__(call, field, replacement)
        yield grant
        if mutation_phase == 2:
            object.__setattr__(call, field, replacement)
        yield grant

    with pytest.raises(PermissionDenied, match="identity"):
        gate.authorize_registered(
            registry, call, stream(), now_ms=10, one_shot=token,
        )
    assert gate._consumed_tokens == set()
    object.__setattr__(call, field, original)
    gate.authorize_registered(registry, call, grants, now_ms=10, one_shot=token)


@pytest.mark.parametrize("field,replacement", [
    ("token_id", "substituted-token"),
    ("request_id", "act_" + "f" * 64),
    ("expires_at_ms", 2_000),
])
@pytest.mark.parametrize("mutation_phase", [1, 2])
def test_registered_token_epoch_precedes_grant_iterator_callbacks(
    field, replacement, mutation_phase,
):
    registry, call, token, grants = _inputs()
    gate = PermissionGate()
    original = getattr(token, field)
    grant = grants[0]

    def stream():
        if mutation_phase == 1:
            object.__setattr__(token, field, replacement)
        yield grant
        if mutation_phase == 2:
            object.__setattr__(token, field, replacement)
        yield grant

    with pytest.raises(PermissionDenied, match="identity"):
        gate.authorize_registered(
            registry, call, stream(), now_ms=10, one_shot=token,
        )
    assert gate._consumed_tokens == set()
    object.__setattr__(token, field, original)
    gate.authorize_registered(registry, call, grants, now_ms=10, one_shot=token)


def test_first_registry_bind_instance_shadow_is_denied_for_read():
    registry, call, _token, grants = _inputs(Effect.READ)
    original_bind = registry.bind
    invoked = []

    def shadowed_bind(current):
        invoked.append(True)
        object.__setattr__(call, "scope", "another-scope")
        return original_bind(current)

    registry.bind = shadowed_bind
    with pytest.raises(
        PermissionDenied,
        match="registered authorization implementation identity changed",
    ):
        PermissionGate().authorize_registered(registry, call, grants, now_ms=10)

    assert invoked == []
    assert call.scope == "fixture"


def test_unchanged_registered_read_and_write_require_no_backend():
    for effect in (Effect.READ, Effect.WRITE):
        registry, call, token, grants = _inputs(effect)
        result = PermissionGate().authorize_registered(
            registry, call, grants, now_ms=10,
            one_shot=token if effect is Effect.WRITE else None,
        )
        assert result.call is call
        assert result.registration.effect is effect
