"""Reject invalid caller clocks before registry binding or grant iteration.

This is a local-only PermissionGate diagnostic. No one-shot is consumed, no
backend runs, no trusted clock/consent is established by any fixture.
"""

from __future__ import annotations

import pytest

from ark.agency.contracts import (
    CapabilityGrant,
    Effect,
    OneShotAuthorization,
    ToolCall,
)
from ark.agency.policy import PermissionGate
from ark.agency.registry import ToolRegistration, ToolRegistry


class _NeverExecute:
    def execute(self, call: ToolCall) -> object:
        raise AssertionError("disconnected backend must never execute")


@pytest.mark.parametrize("effect", (Effect.READ, Effect.WRITE))
@pytest.mark.parametrize("clock", (True, False, -1, 1 << 63, "100", 0.0))
def test_invalid_clock_does_not_bind_registry_or_read_grants(
    monkeypatch: pytest.MonkeyPatch, effect: Effect, clock: object,
) -> None:
    registry = ToolRegistry((
        ToolRegistration(
            "fixture", "scope.readwrite", effect,
            "disconnected-backend", _NeverExecute(),
        ),
    ))
    call = ToolCall("fixture", "scope.readwrite", "synthetic-scope")
    token = OneShotAuthorization("local-token", call.request_id, 1000)
    seen: list[str] = []

    def forbidden_bind(*_args: object, **_kwargs: object) -> object:
        seen.append("BIND")
        raise AssertionError("invalid time reached registry binding")

    def forbidden_grants():
        seen.append("ITERATE")
        raise AssertionError("invalid time reached caller grant generator")
        yield CapabilityGrant("scope.readwrite", "synthetic-scope")

    monkeypatch.setattr(ToolRegistry, "bind", forbidden_bind)
    with pytest.raises(ValueError, match="now_ms"):
        PermissionGate().authorize_registered(
            registry,
            call,
            forbidden_grants(),
            now_ms=clock,  # type: ignore[arg-type]
            one_shot=token,
        )
    assert seen == []


def test_valid_read_clock_still_checks_exact_scope_without_dispatch() -> None:
    registry = ToolRegistry((
        ToolRegistration(
            "fixture", "scope.readwrite", Effect.READ,
            "disconnected-backend", _NeverExecute(),
        ),
    ))
    call = ToolCall("fixture", "scope.readwrite", "synthetic-scope")
    bound = PermissionGate().authorize_registered(
        registry,
        call,
        [CapabilityGrant("scope.readwrite", "synthetic-scope")],
        now_ms=0,
    )
    assert bound.call is call
    assert bound.registration.effect is Effect.READ
