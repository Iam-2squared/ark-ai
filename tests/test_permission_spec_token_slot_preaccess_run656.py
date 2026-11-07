"""Local policy refuses forged ToolSpec and one-shot token descriptors.

No test performs ToolBackend.execute, durable approval, user identity proof,
or externally consequential actions.
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


class _NoExecution:
    def __init__(self):
        self.calls = 0

    def execute(self, _call):
        self.calls += 1
        raise AssertionError("authorization is not tool execution")


def _case(effect):
    backend = _NoExecution()
    call = ToolCall("offline", "synthetic.cap", "fixture")
    spec = ToolSpec("offline", "synthetic.cap", effect)
    grant = CapabilityGrant("synthetic.cap", "fixture", 500)
    token = OneShotAuthorization("local-only", call.request_id, 500)
    registry = ToolRegistry((
        ToolRegistration(
            "offline", "synthetic.cap", effect, "disconnected", backend,
        ),
    ))
    return backend, call, spec, grant, token, registry


@contextmanager
def _poison(cls, member, touched):
    # Preserve exactly the pre-existing class dictionary. Never replace
    # inherited __new__ inside pytest's shared CPython process.
    missing = object()
    old = vars(cls).get(member, missing)

    def malicious(*_args, **_kwargs):
        touched.append(member)
        raise AssertionError("forged policy input descriptor executed")

    replacement = (
        property(malicious)
        if member in ("name", "capability", "effect",
                      "token_id", "request_id", "expires_at_ms")
        else malicious
    )
    setattr(cls, member, replacement)
    try:
        yield
    finally:
        if old is missing:
            delattr(cls, member)
        else:
            setattr(cls, member, old)


@pytest.mark.parametrize("carrier", ("spec", "token"))
@pytest.mark.parametrize(
    "member",
    ("field_1", "field_2", "field_3",
     "__init__", "__post_init__", "__getattribute__", "__getattr__"),
)
@pytest.mark.parametrize(
    "mode",
    ("direct_read", "direct_write", "registered_read", "registered_write"),
)
def test_original_policy_carriers_refuse_poison_before_read_and_spend(
    carrier, member, mode,
):
    effect = Effect.WRITE if mode.endswith("write") else Effect.READ
    backend, call, spec, grant, token, registry = _case(effect)
    cls = ToolSpec if carrier == "spec" else OneShotAuthorization
    fields = (
        ("name", "capability", "effect")
        if carrier == "spec"
        else ("token_id", "request_id", "expires_at_ms")
    )
    name = fields[int(member[-1]) - 1] if member.startswith("field_") else member
    gate = PermissionGate()
    touched = []
    with _poison(cls, name, touched):
        with pytest.raises(
            PermissionDenied,
            match=(
                "tool specification contract changed"
                if carrier == "spec" else "one-shot token contract changed"
            ),
        ):
            if mode.startswith("registered"):
                gate.authorize_registered(
                    registry, call, (grant,), now_ms=100,
                    one_shot=token if effect is Effect.WRITE else None,
                )
            else:
                gate.authorize(
                    spec, call, (grant,), now_ms=100,
                    one_shot=token if effect is Effect.WRITE else None,
                )
    assert touched == []
    assert backend.calls == 0
    assert gate._consumed_tokens == set()


@pytest.mark.parametrize(
    "mode",
    ("direct_read", "direct_write", "registered_read", "registered_write"),
)
def test_unmodified_policy_carriers_retain_local_admission(mode):
    effect = Effect.WRITE if mode.endswith("write") else Effect.READ
    backend, call, spec, grant, token, registry = _case(effect)
    gate = PermissionGate()
    if mode.startswith("registered"):
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
        {"local-only"} if effect is Effect.WRITE else set()
    )
    assert backend.calls == 0
