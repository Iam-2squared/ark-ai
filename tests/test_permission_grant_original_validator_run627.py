"""Do not execute a substituted CapabilityGrant dataclass validation hook.

No backend is invoked, no external permission or actual WRITE is granted.
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


@pytest.mark.parametrize("hook", ("__init__", "__post_init__"))
@pytest.mark.parametrize("effect", (Effect.READ, Effect.WRITE))
def test_counterfeit_grant_validator_denied_before_execution_and_spend(
    monkeypatch, hook, effect,
):
    call = ToolCall("fixture", "read.local", "local", {})
    spec = ToolSpec("fixture", "read.local", effect)
    grant = CapabilityGrant("read.local", "local")
    token = OneShotAuthorization("fixture-approval", call.request_id, 200)
    gate = PermissionGate()
    executed = []

    def hostile(*args, **kwargs):
        executed.append((args, kwargs))
        raise AssertionError("forged grant validator executed")

    monkeypatch.setattr(CapabilityGrant, hook, hostile)
    with pytest.raises(PermissionDenied, match="grant validator changed"):
        gate.authorize(
            spec, call, [grant], now_ms=100,
            one_shot=token if effect is Effect.WRITE else None,
        )
    assert executed == []
    assert gate._consumed_tokens == set()


@pytest.mark.parametrize("effect", (Effect.READ, Effect.WRITE))
def test_original_grant_validator_keeps_normal_local_policy(effect):
    call = ToolCall("fixture", "read.local", "local", {})
    spec = ToolSpec("fixture", "read.local", effect)
    grant = CapabilityGrant("read.local", "local")
    token = OneShotAuthorization("fixture-approval", call.request_id, 200)
    gate = PermissionGate()
    gate.authorize(
        spec, call, [grant], now_ms=100,
        one_shot=token if effect is Effect.WRITE else None,
    )
    assert gate._consumed_tokens == (
        {"fixture-approval"} if effect is Effect.WRITE else set()
    )
