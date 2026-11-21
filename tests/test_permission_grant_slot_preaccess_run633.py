"""Fail closed on forged CapabilityGrant getters before policy reads them.

READ and WRITE are local policy fixtures. No backend dispatch, persisted
approval, external effect or trusted user consent is exercised.
"""

from __future__ import annotations

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


class DisconnectedBackend:
    def execute(self, _call):
        raise AssertionError("no backend may be dispatched")


def _case(effect):
    call = ToolCall("fixture", "read.local", "local", {})
    spec = ToolSpec("fixture", "read.local", effect)
    grant = CapabilityGrant("read.local", "local")
    token = OneShotAuthorization("synthetic-only", call.request_id, 200)
    registry = ToolRegistry((
        ToolRegistration(
            "fixture", "read.local", effect, "inert-backend",
            DisconnectedBackend(),
        ),
    ))
    return call, spec, grant, token, registry


@pytest.mark.parametrize("kind", ("direct", "registered"))
@pytest.mark.parametrize("effect", (Effect.READ, Effect.WRITE))
@pytest.mark.parametrize(
    "member", ("capability", "scope", "expires_at_ms", "__getattribute__", "__getattr__"),
)
def test_preinstalled_grant_slot_or_hook_denied_before_execution_or_token_spend(
    monkeypatch, kind, effect, member,
):
    call, spec, grant, token, registry = _case(effect)
    gate = PermissionGate()
    executed: list[str] = []

    def malicious(*_args, **_kwargs):
        executed.append(member)
        raise AssertionError("forged grant getter ran")

    descriptor = (
        property(malicious) if member in (
            "capability", "scope", "expires_at_ms",
        ) else malicious
    )
    monkeypatch.setattr(CapabilityGrant, member, descriptor, raising=False)
    with pytest.raises(PermissionDenied, match="grant validator changed"):
        if kind == "registered":
            gate.authorize_registered(
                registry, call, (grant,), now_ms=100,
                one_shot=token if effect is Effect.WRITE else None,
            )
        else:
            gate.authorize(
                spec, call, (grant,), now_ms=100,
                one_shot=token if effect is Effect.WRITE else None,
            )
    assert executed == []
    assert gate._consumed_tokens == set()


@pytest.mark.parametrize("kind", ("direct", "registered"))
@pytest.mark.parametrize("effect", (Effect.READ, Effect.WRITE))
def test_grant_generator_rebind_on_exhaustion_denied_before_getter_or_spend(
    monkeypatch, kind, effect,
):
    call, spec, grant, token, registry = _case(effect)
    gate = PermissionGate()
    invoked: list[str] = []

    def malicious(_self):
        invoked.append("scope")
        raise AssertionError("forged grant slot ran")

    def grants():
        yield grant
        # Iteration/StopIteration is also a callback boundary, even after
        # a matching grant has already been examined.
        monkeypatch.setattr(CapabilityGrant, "scope", property(malicious))

    with pytest.raises(PermissionDenied, match="grant validator changed"):
        if kind == "registered":
            gate.authorize_registered(
                registry, call, grants(), now_ms=100,
                one_shot=token if effect is Effect.WRITE else None,
            )
        else:
            gate.authorize(
                spec, call, grants(), now_ms=100,
                one_shot=token if effect is Effect.WRITE else None,
            )
    assert invoked == []
    assert gate._consumed_tokens == set()


@pytest.mark.parametrize("kind", ("direct", "registered"))
@pytest.mark.parametrize("effect", (Effect.READ, Effect.WRITE))
def test_original_grant_slots_preserve_local_deny_only_policy(kind, effect):
    call, spec, grant, token, registry = _case(effect)
    gate = PermissionGate()
    if kind == "registered":
        bound = gate.authorize_registered(
            registry, call, (grant,), now_ms=100,
            one_shot=token if effect is Effect.WRITE else None,
        )
        assert bound.call is call
    else:
        gate.authorize(
            spec, call, (grant,), now_ms=100,
            one_shot=token if effect is Effect.WRITE else None,
        )
    assert gate._consumed_tokens == (
        {"synthetic-only"} if effect is Effect.WRITE else set()
    )
