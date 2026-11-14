"""Registry-authoritative permission diagnostics with no backend execution."""

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


class _DisconnectedBackend:
    def __init__(self):
        self.calls = 0

    def execute(self, call):
        self.calls += 1
        raise AssertionError("fixture backend must never execute")


def _registry(effect):
    backend = _DisconnectedBackend()
    registration = ToolRegistration(
        "synthetic.tool", "synthetic.capability", effect, "offline-backend", backend
    )
    return ToolRegistry((registration,)), backend, registration


def _call():
    return ToolCall("synthetic.tool", "synthetic.capability", "scope:fixture")


def _grant():
    return CapabilityGrant("synthetic.capability", "scope:fixture")


def test_registered_read_returns_same_identity_without_dispatch():
    registry, backend, _ = _registry(Effect.READ)
    call = _call()
    bound = PermissionGate().authorize_registered(registry, call, [_grant()], now_ms=10)
    expected = registry.bind(call)
    assert bound.registry_revision == expected.registry_revision
    assert bound.bound_action_id == expected.bound_action_id
    assert bound.registration is expected.registration
    assert backend.calls == 0


def test_registered_write_cannot_be_downgraded_to_read():
    registry, backend, _ = _registry(Effect.WRITE)
    with pytest.raises(PermissionDenied, match="one-shot"):
        PermissionGate().authorize_registered(registry, _call(), [_grant()], now_ms=10)
    assert backend.calls == 0


def test_registered_write_consumes_only_one_matching_token():
    registry, backend, _ = _registry(Effect.WRITE)
    gate = PermissionGate()
    call = _call()
    token = OneShotAuthorization("synthetic-token", call.request_id, 100)
    gate.authorize_registered(registry, call, [_grant()], now_ms=10, one_shot=token)
    with pytest.raises(PermissionDenied, match="already consumed"):
        gate.authorize_registered(registry, call, [_grant()], now_ms=10, one_shot=token)
    assert backend.calls == 0


@pytest.mark.parametrize(
    "call",
    [
        ToolCall("unknown.tool", "synthetic.capability", "scope:fixture"),
        ToolCall("synthetic.tool", "wrong.capability", "scope:fixture"),
    ],
)
def test_unknown_or_mismatched_registered_call_is_denied(call):
    registry, backend, _ = _registry(Effect.READ)
    with pytest.raises(PermissionDenied, match="registry binding"):
        PermissionGate().authorize_registered(registry, call, [_grant()], now_ms=10)
    assert backend.calls == 0


def test_grant_iteration_cannot_replace_bound_request_identity():
    registry, backend, _ = _registry(Effect.WRITE)
    gate = PermissionGate()
    call = _call()
    token = OneShotAuthorization("stable-token", call.request_id, 100)

    def mutating_grants():
        yield _grant()
        object.__setattr__(call, "scope", "scope:other")

    with pytest.raises(PermissionDenied, match="identity changed"):
        gate.authorize_registered(
            registry, call, mutating_grants(), now_ms=10, one_shot=token
        )
    assert backend.calls == 0
    object.__setattr__(call, "scope", "scope:fixture")
    gate.authorize_registered(registry, call, [_grant()], now_ms=10, one_shot=token)
    assert backend.calls == 0


def test_reflected_registry_mutation_during_grants_denies_before_token_consumption():
    registry, backend, registration = _registry(Effect.WRITE)
    gate = PermissionGate()
    call = _call()
    token = OneShotAuthorization("stable-token", call.request_id, 100)

    def mutating_grants():
        yield _grant()
        object.__setattr__(registration, "effect", Effect.READ)

    with pytest.raises(PermissionDenied, match="registry binding"):
        gate.authorize_registered(
            registry, call, mutating_grants(), now_ms=10, one_shot=token
        )
    assert backend.calls == 0
    object.__setattr__(registration, "effect", Effect.WRITE)
    gate.authorize_registered(registry, call, [_grant()], now_ms=10, one_shot=token)
    assert backend.calls == 0


def test_imitation_registry_is_denied():
    with pytest.raises(PermissionDenied, match="exact registry"):
        PermissionGate().authorize_registered(
            object(), _call(), [_grant()], now_ms=10
        )


def test_grants_must_match_exact_scope_and_expiry():
    registry, backend, _ = _registry(Effect.READ)
    for grant in (
        CapabilityGrant("synthetic.capability", "scope:other"),
        CapabilityGrant("synthetic.capability", "scope:fixture", expires_at_ms=10),
    ):
        with pytest.raises(PermissionDenied, match="no active"):
            PermissionGate().authorize_registered(registry, _call(), [grant], now_ms=10)
    assert backend.calls == 0
