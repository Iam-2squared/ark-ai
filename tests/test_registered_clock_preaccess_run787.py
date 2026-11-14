"""Registered policy rejects invalid clocks before callback-bearing inputs.

Disconnected fixture backends are never dispatched. Local one-shot admission
does not prove trusted time, durable permission or real-world effects.
"""

import pytest

from ark.agency.contracts import (
    CapabilityGrant,
    Effect,
    OneShotAuthorization,
    ToolCall,
)
from ark.agency.policy import PermissionGate
from ark.agency.registry import ToolRegistration, ToolRegistry


class NeverExecute:
    def __init__(self):
        self.calls = 0

    def execute(self, _call):
        self.calls += 1
        raise AssertionError("registered policy must never dispatch fixture backend")


def _case(effect):
    backend = NeverExecute()
    registry = ToolRegistry((
        ToolRegistration(
            "fixture.clock", "fixture.capability", effect, "fixture-backend", backend,
        ),
    ))
    call = ToolCall("fixture.clock", "fixture.capability", "fixture:scope")
    grant = CapabilityGrant("fixture.capability", "fixture:scope")
    token = (
        OneShotAuthorization("fixture-token", call.request_id, 100)
        if effect is Effect.WRITE else None
    )
    return backend, registry, call, grant, token


@pytest.mark.parametrize("effect", (Effect.READ, Effect.WRITE))
@pytest.mark.parametrize("invalid", (None, True, -1, 1.0, "10", 2**63))
def test_invalid_registered_clock_refuses_registry_and_grant_callbacks(
    monkeypatch, effect, invalid,
):
    backend, registry, call, grant, token = _case(effect)
    gate = PermissionGate()
    callbacks = []

    def hostile_bind(*args, **kwargs):
        callbacks.append("registry")
        raise AssertionError("registry was accessed before clock validation")

    class HostileGrants:
        def __iter__(self):
            callbacks.append("grants")
            yield grant

    with monkeypatch.context() as patch:
        patch.setattr(ToolRegistry, "bind", hostile_bind)
        with pytest.raises(ValueError, match="now_ms must be a non-negative integer"):
            gate.authorize_registered(
                registry, call, HostileGrants(), now_ms=invalid,
                one_shot=token,
            )
    assert callbacks == []
    assert gate._consumed_tokens == set()
    assert backend.calls == 0

    # The refused preflight did not spend any local one-shot token.
    bound = gate.authorize_registered(
        registry, call, (grant,), now_ms=10, one_shot=token,
    )
    assert bound.call is call
    assert backend.calls == 0
    assert gate._consumed_tokens == (
        {"fixture-token"} if effect is Effect.WRITE else set()
    )


@pytest.mark.parametrize("valid", (0, 2**63 - 1))
def test_registered_read_clock_boundaries_are_locally_accepted(valid):
    backend, registry, call, grant, _token = _case(Effect.READ)
    result = PermissionGate().authorize_registered(
        registry, call, (grant,), now_ms=valid,
    )
    assert result.call is call
    assert backend.calls == 0
