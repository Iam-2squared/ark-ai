"""Exact original grant-carrier custody in local-only PermissionGate checks.

Reflected mutable frozen grants can gain equal-valued replacement strings.
No real issuer, durable approval or backend execution is established here.
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
def test_registered_bind_instance_shadow_is_denied_before_grant_callback(
    monkeypatch, effect,
):
    gate, registry, _spec, call, grant, token = _fixture(effect)
    invoked = []
    original_bind = registry.bind

    def shadowed_bind(current):
        invoked.append(True)
        return original_bind(current)

    monkeypatch.setattr(registry, "bind", shadowed_bind)
    with pytest.raises(
        PermissionDenied,
        match="registered authorization implementation identity changed",
    ):
        gate.authorize_registered(
            registry, call, (grant,), now_ms=10,
            one_shot=token if effect is Effect.WRITE else None,
        )

    assert invoked == []
    assert grant.scope == "offline"
    assert gate._consumed_tokens == set()

def test_reflective_token_ledger_replacement_is_denied_before_registered_binding():
    gate, registry, _spec, call, grant, token = _fixture()
    original_ledger = gate._consumed_tokens
    replacement = set()
    object.__setattr__(gate, "_consumed_tokens", replacement)

    with pytest.raises(PermissionDenied, match="state changed outside token spend"):
        gate.authorize_registered(
            registry, call, (grant,), now_ms=10, one_shot=token,
        )

    assert original_ledger == set()
    assert replacement == set()


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
