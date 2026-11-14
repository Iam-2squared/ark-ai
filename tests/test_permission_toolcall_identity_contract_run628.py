"""A direct capability grant cannot trust a substituted ToolCall digest.

Only process-local one-shot tokens and in-memory calls are exercised here.
These checks never dispatch a backend or authorize an external write.
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


def _inputs(effect):
    call = ToolCall("fixture", "capability", "local-only", {"k": 1})
    spec = ToolSpec("fixture", "capability", effect)
    grant = CapabilityGrant("capability", "local-only")
    token = OneShotAuthorization("local-test-token", call.request_id, 200)
    return call, spec, grant, token


@pytest.mark.parametrize("effect", (Effect.READ, Effect.WRITE))
@pytest.mark.parametrize(
    "descriptor",
    ("request_id", "arguments_sha256", "__init__", "__post_init__"),
)
def test_preinstalled_toolcall_identity_replacement_never_runs(
    monkeypatch, effect, descriptor,
):
    call, spec, grant, token = _inputs(effect)
    gate = PermissionGate()
    executed = []

    def hostile(*args, **kwargs):
        executed.append((args, kwargs))
        raise AssertionError("ToolCall counterfeit executed")

    replacement = (
        property(hostile)
        if descriptor in ("request_id", "arguments_sha256") else hostile
    )
    monkeypatch.setattr(ToolCall, descriptor, replacement)
    with pytest.raises(PermissionDenied, match="ToolCall identity contract changed"):
        gate.authorize(
            spec, call, [grant], now_ms=100,
            one_shot=token if effect is Effect.WRITE else None,
        )
    assert executed == []
    assert gate._consumed_tokens == set()


@pytest.mark.parametrize("effect", (Effect.READ, Effect.WRITE))
def test_grant_generator_cannot_replace_request_digest_before_spend(
    monkeypatch, effect,
):
    call, spec, grant, token = _inputs(effect)
    gate = PermissionGate()
    executed = []

    def hostile(self):
        executed.append(True)
        raise AssertionError("replacement request_id executed")

    def grants():
        monkeypatch.setattr(ToolCall, "request_id", property(hostile))
        yield grant

    with pytest.raises(PermissionDenied, match="ToolCall identity contract changed"):
        gate.authorize(
            spec, call, grants(), now_ms=100,
            one_shot=token if effect is Effect.WRITE else None,
        )
    assert executed == []
    assert gate._consumed_tokens == set()


@pytest.mark.parametrize("effect", (Effect.READ, Effect.WRITE))
def test_unchanged_request_contract_keeps_local_policy(effect):
    call, spec, grant, token = _inputs(effect)
    gate = PermissionGate()
    gate.authorize(
        spec, call, [grant], now_ms=100,
        one_shot=token if effect is Effect.WRITE else None,
    )
    assert gate._consumed_tokens == (
        {"local-test-token"} if effect is Effect.WRITE else set()
    )
