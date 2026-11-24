"""Run1323: registered authorization pins ToolRegistry lookup hooks.

Only an inert local registry/backend is used. No tool is dispatched and no
durable approval, trusted clock or external exactly-once effect is claimed.
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


class _NeverExecute:
    def __init__(self) -> None:
        self.calls = 0

    def execute(self, _call: ToolCall) -> object:
        self.calls += 1
        raise AssertionError("registered authorization must not dispatch")


def _fixture():
    backend = _NeverExecute()
    registration = ToolRegistration(
        "fixture.write", "fixture.write", Effect.WRITE,
        "disconnected.mock.v1", backend,
    )
    registry = ToolRegistry((registration,))
    call = ToolCall(
        "fixture.write", "fixture.write", "synthetic:scope",
        {"value": "local-only"},
    )
    gate = PermissionGate()
    grant = CapabilityGrant("fixture.write", "synthetic:scope")
    token = OneShotAuthorization("synthetic-token", call.request_id, 500)
    return backend, registration, registry, call, gate, grant, token


@pytest.mark.parametrize("hook", ("__getattribute__", "__getattr__"))
def test_registered_write_rejects_replaced_registry_lookup_hook_before_callbacks(
    hook: str, monkeypatch: pytest.MonkeyPatch,
) -> None:
    backend, _registration, registry, call, gate, grant, token = _fixture()
    invoked: list[str] = []
    iterated: list[str] = []

    def forbidden(*_args: object, **_kwargs: object) -> None:
        invoked.append(hook)
        raise AssertionError("substituted registry lookup hook must not execute")

    def grants():
        iterated.append("started")
        yield grant

    with monkeypatch.context() as patch:
        patch.setattr(ToolRegistry, hook, forbidden, raising=False)
        with pytest.raises(
            PermissionDenied,
            match="registered authorization lookup hook changed",
        ):
            gate.authorize_registered(
                registry, call, grants(), now_ms=100, one_shot=token,
            )

    assert invoked == []
    assert iterated == []
    assert token.token_id not in gate._consumed_tokens
    assert backend.calls == 0
