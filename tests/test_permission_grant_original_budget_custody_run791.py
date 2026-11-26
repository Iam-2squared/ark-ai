"""Run791: exact grant budget baseline must not invoke untrusted equality.

Only in-process synthetic authorization admission is exercised; no backend is
run, no durable human consent is established and no token means real dispatch.
"""

from __future__ import annotations

import pytest

from ark.agency import policy
from ark.agency.contracts import (
    CapabilityGrant,
    Effect,
    OneShotAuthorization,
    PermissionDenied,
    ToolCall,
    ToolSpec,
)
from ark.agency.registry import ToolRegistration, ToolRegistry


class NeverExecute:
    def __init__(self) -> None:
        self.calls = 0

    def execute(self, _call: ToolCall) -> None:
        self.calls += 1
        raise AssertionError("synthetic admission must never dispatch")


class PoisonComparison:
    def __eq__(self, _other: object) -> bool:
        raise AssertionError("budget equality should not run")

    def __ne__(self, _other: object) -> bool:
        raise AssertionError("budget inequality should not run")


@pytest.mark.parametrize("registered", (False, True))
@pytest.mark.parametrize("baseline", (1024.0, PoisonComparison()))
def test_original_grant_budget_replacement_denied_before_iterator_and_spend(
    registered: bool, baseline: object, monkeypatch: pytest.MonkeyPatch,
) -> None:
    backend = NeverExecute()
    call = ToolCall("fixture.tool", "fixture.write", "scope:private")
    spec = ToolSpec("fixture.tool", "fixture.write", Effect.WRITE)
    registry = ToolRegistry((
        ToolRegistration(
            "fixture.tool", "fixture.write", Effect.WRITE, "local", backend,
        ),
    ))
    grant = CapabilityGrant("fixture.write", "scope:private")
    token = OneShotAuthorization("synthetic-token", call.request_id, 100)
    gate = policy.PermissionGate()
    visited: list[str] = []

    def grants():
        visited.append("grant")
        yield grant

    with monkeypatch.context() as patch:
        patch.setattr(policy, "_ORIGINAL_MAX_GRANTS", baseline)
        with pytest.raises(PermissionDenied, match="grant budget contract changed"):
            if registered:
                gate.authorize_registered(
                    registry, call, grants(), now_ms=10, one_shot=token,
                )
            else:
                gate.authorize(
                    spec, call, grants(), now_ms=10, one_shot=token,
                )
    assert visited == []
    assert gate._consumed_tokens == set()
    assert backend.calls == 0

    # After restoring the reviewed constant, the synthetic gate still admits
    # exactly one local request without invoking the backend.
    if registered:
        gate.authorize_registered(
            registry, call, [grant], now_ms=10, one_shot=token,
        )
    else:
        gate.authorize(spec, call, [grant], now_ms=10, one_shot=token)
    assert gate._consumed_tokens == {"synthetic-token"}
    assert backend.calls == 0
