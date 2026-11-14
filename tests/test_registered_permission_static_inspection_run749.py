"""Run749: policy static lookup is a protected local authorization boundary.

All tools are inert mock backends. No external action, durable user grant,
trusted clock, or exactly-once effect is established by these checks.
"""

from types import SimpleNamespace

import pytest

from ark.agency import policy
from ark.agency.contracts import (
    CapabilityGrant,
    Effect,
    OneShotAuthorization,
    PermissionDenied,
    ToolCall,
)
from ark.agency.registry import ToolRegistration, ToolRegistry


class _NeverExecute:
    def __init__(self):
        self.calls = 0

    def execute(self, _call):
        self.calls += 1
        raise AssertionError("registered policy diagnostic dispatched backend")


def _setup(effect):
    backend = _NeverExecute()
    registry = ToolRegistry((
        ToolRegistration("fixture.read", "fixture.capability", effect,
                         "inert-backend", backend),
    ))
    call = ToolCall("fixture.read", "fixture.capability", "fixture:scope")
    grant = CapabilityGrant("fixture.capability", "fixture:scope")
    gate = policy.PermissionGate()
    token = (OneShotAuthorization("fixture-token", call.request_id, 100)
             if effect is Effect.WRITE else None)
    return backend, registry, call, grant, gate, token


@pytest.mark.parametrize("effect", (Effect.READ, Effect.WRITE))
@pytest.mark.parametrize("replacement", ("inspect_module", "static_lookup"))
def test_replaced_static_inspection_denied_before_lookup_and_token_spend(
    monkeypatch, effect, replacement,
):
    backend, registry, call, grant, gate, token = _setup(effect)
    called = []

    def poisoned(*args, **kwargs):
        called.append((args, kwargs))
        raise AssertionError("substituted static inspection called")

    with monkeypatch.context() as patch:
        if replacement == "inspect_module":
            patch.setattr(policy, "inspect", SimpleNamespace(getattr_static=poisoned))
        else:
            patch.setattr(policy.inspect, "getattr_static", poisoned)
        with pytest.raises(
            PermissionDenied, match="static inspection changed",
        ):
            gate.authorize_registered(
                registry, call, (grant,), now_ms=10, one_shot=token,
            )
    assert called == []
    # The rejected attempt must not spend the process-local WRITE token.
    bound = gate.authorize_registered(
        registry, call, (grant,), now_ms=10, one_shot=token,
    )
    assert bound.registration.backend is backend
    assert bound.call is call
    assert backend.calls == 0


def test_normal_registered_policy_never_invokes_backend():
    backend, registry, call, grant, gate, _ = _setup(Effect.READ)
    bound = gate.authorize_registered(registry, call, (grant,), now_ms=10)
    assert bound.call.request_id == call.request_id
    assert backend.calls == 0
