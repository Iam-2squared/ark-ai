"""Registry-bound policy admission never dispatches a synthetic backend.

Local PermissionGate decisions do not prove retained one-shot authorization,
trusted time, durable audit or permission for real-world WRITE effects.
"""

from __future__ import annotations

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


class NeverExecuteBackend:
    def __init__(self) -> None:
        self.calls = 0

    def execute(self, _call: ToolCall) -> object:
        self.calls += 1
        raise AssertionError("registered approval must never execute a backend")


def _bound_inputs(effect: Effect):
    backend = NeverExecuteBackend()
    registry = ToolRegistry((
        ToolRegistration("synthetic.action", "synthetic.scope", effect, "mock", backend),
    ))
    call = ToolCall("synthetic.action", "synthetic.scope", "sandbox:one", {"v": 1})
    grant = CapabilityGrant("synthetic.scope", "sandbox:one")
    return registry, call, grant, backend


def test_read_registry_policy_never_dispatches_backend() -> None:
    registry, call, grant, backend = _bound_inputs(Effect.READ)
    bound = PermissionGate().authorize_registered(
        registry, call, (grant,), now_ms=100,
    )
    assert bound.call is call
    assert bound.registration is registry.get("synthetic.action")
    assert bound.registry_revision == registry.revision
    assert backend.calls == 0


@pytest.mark.parametrize("denial", ("no_token", "wrong_scope", "expired_grant"))
def test_registered_write_denials_preserve_backend_nonexecution(denial: str) -> None:
    registry, call, grant, backend = _bound_inputs(Effect.WRITE)
    token = OneShotAuthorization("inert-token", call.request_id, 1000)
    if denial == "no_token":
        decision = None
        grants = (grant,)
    elif denial == "wrong_scope":
        decision = token
        grants = (CapabilityGrant(grant.capability, "sandbox:other"),)
    else:
        decision = token
        grants = (CapabilityGrant(grant.capability, grant.scope, 100),)
    gate = PermissionGate()
    with pytest.raises(PermissionDenied):
        gate.authorize_registered(
            registry, call, grants, now_ms=100, one_shot=decision,
        )
    assert backend.calls == 0
    if decision is not None:
        assert token.token_id not in gate._consumed_tokens


def test_registered_write_token_spend_is_local_and_never_dispatches() -> None:
    registry, call, grant, backend = _bound_inputs(Effect.WRITE)
    token = OneShotAuthorization("inert-token", call.request_id, 1000)
    first = PermissionGate()
    bound = first.authorize_registered(
        registry, call, (grant,), now_ms=100, one_shot=token,
    )
    assert bound.registration.effect is Effect.WRITE
    assert backend.calls == 0
    with pytest.raises(PermissionDenied):
        first.authorize_registered(
            registry, call, (grant,), now_ms=100, one_shot=token,
        )
    # A fresh gate cannot inherit a process-local token spend. This is a
    # missing durability proof, not a legitimate second real-world WRITE.
    restarted = PermissionGate()
    assert token.token_id not in restarted._consumed_tokens
    restarted.authorize_registered(
        registry, call, (grant,), now_ms=100, one_shot=token,
    )
    assert backend.calls == 0


def test_registry_bound_write_cannot_be_downgraded_by_caller_arguments() -> None:
    registry, call, grant, backend = _bound_inputs(Effect.WRITE)
    gate = PermissionGate()
    with pytest.raises(PermissionDenied):
        gate.authorize_registered(registry, call, (grant,), now_ms=100)
    assert registry.get("synthetic.action").effect is Effect.WRITE
    assert backend.calls == 0
