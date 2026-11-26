"""Fail closed on replaced ToolCall slots before identity or grant access.

Every case is disconnected. Neither a local one-shot token nor a registry
binding proves external authorization or permits backend execution.
"""

from contextlib import contextmanager

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


class _NeverDispatch:
    def __init__(self):
        self.calls = 0

    def execute(self, _call):
        self.calls += 1
        raise AssertionError("registry admission is not tool execution")


def _case(effect=Effect.WRITE):
    backend = _NeverDispatch()
    call = ToolCall("fixture.tool", "fixture.cap", "offline", {"ok": True})
    registry = ToolRegistry((
        ToolRegistration(
            "fixture.tool", "fixture.cap", effect, "disconnected", backend,
        ),
    ))
    spec = ToolSpec("fixture.tool", "fixture.cap", effect)
    grant = CapabilityGrant("fixture.cap", "offline", 200)
    token = OneShotAuthorization("synthetic-token", call.request_id, 200)
    return backend, call, registry, spec, grant, token


@contextmanager
def _poison_slot(member, invoked):
    # Restore the exact original class dictionary, not just an inherited
    # object.__getattribute__ as a new own attribute. Never patch __new__ in
    # the shared pytest interpreter: CPython tp_new can remain contaminated.
    missing = object()
    previous = vars(ToolCall).get(member, missing)

    def malicious(*_args, **_kwargs):
        invoked.append(member)
        raise AssertionError("forged ToolCall accessor must not run")

    descriptor = (
        property(malicious)
        if member in ("tool", "capability", "scope", "arguments")
        else malicious
    )
    setattr(ToolCall, member, descriptor)
    try:
        yield
    finally:
        if previous is missing:
            delattr(ToolCall, member)
        else:
            setattr(ToolCall, member, previous)


@pytest.mark.parametrize(
    "member",
    ("tool", "capability", "scope", "arguments",
     "__getattribute__", "__getattr__"),
)
@pytest.mark.parametrize(
    "operation",
    ("resolve", "bind", "direct_read", "registered_read",
     "direct_write", "registered_write"),
)
def test_preinstalled_toolcall_slot_rejected_before_execution_or_token(
    member, operation,
):
    effect = Effect.READ if operation.endswith("read") else Effect.WRITE
    backend, call, registry, spec, grant, token = _case(effect)
    invoked = []
    gate = PermissionGate()
    with _poison_slot(member, invoked):
        if operation in ("resolve", "bind"):
            with pytest.raises(
                ValueError, match="ToolCall identity constructor changed",
            ):
                getattr(registry, operation)(call)
        elif operation.startswith("registered"):
            with pytest.raises(
                PermissionDenied, match="ToolCall identity contract changed",
            ):
                gate.authorize_registered(
                    registry, call, (grant,), now_ms=100,
                    one_shot=token if effect is Effect.WRITE else None,
                )
        else:
            with pytest.raises(
                PermissionDenied, match="ToolCall identity contract changed",
            ):
                gate.authorize(
                    spec, call, (grant,), now_ms=100,
                    one_shot=token if effect is Effect.WRITE else None,
                )
    assert invoked == []
    assert backend.calls == 0
    assert gate._consumed_tokens == set()


@pytest.mark.parametrize(
    "operation",
    ("resolve", "bind", "direct_read", "registered_read",
     "direct_write", "registered_write"),
)
def test_original_toolcall_carrier_preserves_disconnected_policy(operation):
    effect = Effect.READ if operation.endswith("read") else Effect.WRITE
    backend, call, registry, spec, grant, token = _case(effect)
    gate = PermissionGate()
    if operation in ("resolve", "bind"):
        assert getattr(registry, operation)(call)
    elif operation.startswith("registered"):
        assert gate.authorize_registered(
            registry, call, (grant,), now_ms=100,
            one_shot=token if effect is Effect.WRITE else None,
        ).call is call
    else:
        gate.authorize(
            spec, call, (grant,), now_ms=100,
            one_shot=token if effect is Effect.WRITE else None,
        )
    assert gate._consumed_tokens == (
        {"synthetic-token"} if effect is Effect.WRITE
        and operation not in ("resolve", "bind") else set()
    )
    assert backend.calls == 0
