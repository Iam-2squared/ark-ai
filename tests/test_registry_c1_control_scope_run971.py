"""Run971: C1 terminal controls cannot enter registered action identities.

These are disconnected identity tests. Neither a bound action nor an in-memory
one-shot check establishes trusted approval or authorizes backend dispatch.
The generic/frozen ToolCall contract is intentionally unchanged.
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

# C1 codes other than U+0085 (covered by the earlier Unicode-format matrix).
_C1 = ("\u0080", "\u0081", "\u008d", "\u0090", "\u009b", "\u009f")


class _NeverExecute:
    def __init__(self) -> None:
        self.calls = 0

    def execute(self, _call: ToolCall) -> object:
        self.calls += 1
        raise AssertionError("registered identity review must never execute")


@pytest.mark.parametrize("control", _C1)
@pytest.mark.parametrize("field", ("name", "capability", "backend_id"))
def test_c1_registration_rejected_before_registry_or_backend(control: str, field: str) -> None:
    backend = _NeverExecute()
    values = {
        "name": "local.echo",
        "capability": "local.read",
        "backend_id": "fixture.mock",
    }
    values[field] += control + "spoof"
    with pytest.raises(ValueError, match="Unicode formatting control"):
        ToolRegistration(
            values["name"], values["capability"], Effect.READ, values["backend_id"], backend,
        )
    assert backend.calls == 0


@pytest.mark.parametrize("control", _C1)
@pytest.mark.parametrize("operation", ("resolve", "bind"))
def test_c1_scope_rejected_for_read_and_write_binding(control: str, operation: str) -> None:
    backend = _NeverExecute()
    registry = ToolRegistry((
        ToolRegistration("local.echo", "local.read", Effect.WRITE, "fixture.mock", backend),
    ))
    # Frozen generic ToolCall still admits opaque scope labels; only the
    # opt-in registered boundary applies the C1 delimiter restriction.
    call = ToolCall("local.echo", "local.read", "private" + control + "spoof")
    with pytest.raises(ValueError, match="Unicode formatting control"):
        getattr(registry, operation)(call)
    assert backend.calls == 0


@pytest.mark.parametrize("control", ("\u009b", "\u009f"))
def test_rejected_c1_write_does_not_consume_unrelated_local_token(control: str) -> None:
    backend = _NeverExecute()
    registry = ToolRegistry((
        ToolRegistration("local.write", "local.write", Effect.WRITE, "fixture.mock", backend),
    ))
    good = ToolCall("local.write", "local.write", "private")
    bad = ToolCall("local.write", "local.write", "private" + control + "spoof")
    grant = CapabilityGrant("local.write", "private", expires_at_ms=1000)
    token = OneShotAuthorization("fixture-only", good.request_id, expires_at_ms=1000)
    gate = PermissionGate()

    with pytest.raises(PermissionDenied, match="registry binding"):
        gate.authorize_registered(registry, bad, (grant,), now_ms=100, one_shot=token)
    bound = gate.authorize_registered(registry, good, (grant,), now_ms=100, one_shot=token)
    assert bound.call is good
    with pytest.raises(PermissionDenied):
        gate.authorize_registered(registry, good, (grant,), now_ms=100, one_shot=token)
    assert backend.calls == 0


def test_local_multilingual_registered_identifiers_remain_valid() -> None:
    backend = _NeverExecute()
    registry = ToolRegistry((
        ToolRegistration("検索", "端末情報", Effect.READ, "現地mock", backend),
    ))
    call = ToolCall("検索", "端末情報", "東京/個人")
    assert registry.resolve(call).name == "検索"
    assert registry.bind(call).call is call
    assert backend.calls == 0
