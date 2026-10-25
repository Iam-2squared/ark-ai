"""Exact original policy carriers must survive WRITE approval callbacks.

All grants, identities and tokens are synthetic. Token consumption is only
process-local and never conveys durable consent or dispatch authority.
"""

from threading import Lock

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


class NoBackend:
    def __init__(self):
        self.calls = 0

    def execute(self, _call):
        self.calls += 1
        raise AssertionError("permission tests must not dispatch")


def _case():
    call = ToolCall("fixture", "mock.write", "offline")
    spec = ToolSpec("fixture", "mock.write", Effect.WRITE)
    grant = CapabilityGrant("mock.write", "offline", 1000)
    token = OneShotAuthorization("local-token-unique", call.request_id, 1000)
    backend = NoBackend()
    registry = ToolRegistry((
        ToolRegistration("fixture", "mock.write", Effect.WRITE, "mock", backend),
    ))
    return PermissionGate(), spec, call, grant, token, registry, backend


def _distinct(value):
    if type(value) is int:
        copy = int(str(value))
    else:
        copy = ("!" + value)[1:]
    assert copy == value and copy is not value
    return copy


def _carrier_to_mutate(case, field):
    _gate, spec, call, _grant, token, _registry, _backend = case
    if field.startswith("spec_"):
        return spec, field.removeprefix("spec_")
    if field.startswith("call_"):
        return call, field.removeprefix("call_")
    return token, field.removeprefix("token_")


@pytest.mark.parametrize("registered", (False, True))
@pytest.mark.parametrize("phase", ("grants", "spend"))
@pytest.mark.parametrize("field", (
    "call_tool",
    "call_capability",
    "call_scope",
    "token_token_id",
    "token_request_id",
    "token_expires_at_ms",
))
def test_equal_value_original_call_or_token_swap_never_spends(
    registered, phase, field,
):
    case = _case()
    gate, spec, call, grant, token, registry, backend = case
    target, attr = _carrier_to_mutate(case, field)
    original = getattr(target, attr)
    modified = []

    def mutate():
        assert not modified
        object.__setattr__(target, attr, _distinct(original))
        modified.append(True)

    def grants():
        yield grant
        if phase == "grants":
            mutate()

    class MutatingSpendLock:
        def __enter__(self):
            mutate()
            return self

        def __exit__(self, exc_type, exc, tb):
            return False

    if phase == "spend":
        gate._token_lock = MutatingSpendLock()
    with pytest.raises(PermissionDenied, match="identity|input changed"):
        if registered:
            gate.authorize_registered(
                registry, call, grants(), now_ms=10, one_shot=token,
            )
        else:
            gate.authorize(spec, call, grants(), now_ms=10, one_shot=token)
    assert modified == [True]
    assert gate._consumed_tokens == set()
    assert backend.calls == 0


@pytest.mark.parametrize("phase", ("grants", "spend"))
@pytest.mark.parametrize("field", ("spec_name", "spec_capability"))
def test_equal_value_tool_spec_swap_cannot_authorize_direct_write(phase, field):
    case = _case()
    gate, spec, call, grant, token, _registry, backend = case
    target, attr = _carrier_to_mutate(case, field)
    original = getattr(target, attr)
    modified = []

    def mutate():
        object.__setattr__(target, attr, _distinct(original))
        modified.append(True)

    def grants():
        yield grant
        if phase == "grants":
            mutate()

    class MutatingSpendLock:
        def __enter__(self):
            mutate()
            return self

        def __exit__(self, exc_type, exc, tb):
            return False

    if phase == "spend":
        gate._token_lock = MutatingSpendLock()
    with pytest.raises(PermissionDenied, match="input changed"):
        gate.authorize(spec, call, grants(), now_ms=10, one_shot=token)
    assert modified == [True]
    assert gate._consumed_tokens == set()
    assert backend.calls == 0


@pytest.mark.parametrize("registered", (False, True))
def test_unchanged_policy_still_spends_once_without_dispatch(registered):
    gate, spec, call, grant, token, registry, backend = _case()
    gate._token_lock = Lock()
    if registered:
        result = gate.authorize_registered(
            registry, call, (grant,), now_ms=10, one_shot=token,
        )
        assert result.call is call
    else:
        assert gate.authorize(
            spec, call, (grant,), now_ms=10, one_shot=token,
        ) is None
    assert gate._consumed_tokens == {"local-token-unique"}
    assert backend.calls == 0
