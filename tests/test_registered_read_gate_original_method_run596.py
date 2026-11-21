"""Registered READ preflight must not trust a substituted PermissionGate method.

All inputs are offline and backend.execute is forbidden. These checks prove
neither durable grant custody nor permission for an actual external READ.
"""

import pytest

from ark.agency.contracts import CapabilityGrant, Effect, ToolCall
from ark.agency.disconnected_registered_read_preflight import (
    DisconnectedReadPreflightRejected,
    review_disconnected_registered_read,
)
from ark.agency.policy import PermissionGate
from ark.agency.registry import ToolRegistration, ToolRegistry


class _NoBackend:
    def __init__(self):
        self.calls = 0

    def execute(self, call):
        self.calls += 1
        raise AssertionError("synthetic READ must never execute")


def _inputs():
    backend = _NoBackend()
    registry = ToolRegistry((
        ToolRegistration("local.read", "local.read", Effect.READ, "offline", backend),
    ))
    call = ToolCall("local.read", "local.read", "fixture", {"x": 1})
    grant = CapabilityGrant("local.read", "fixture", expires_at_ms=100)
    return registry, PermissionGate(), call, (grant,), backend


def _review(items):
    registry, gate, call, grants, _backend = items
    return review_disconnected_registered_read(
        registry, gate, call, grants, now_ms=10,
    )


@pytest.mark.parametrize("scope", ("class", "instance"))
@pytest.mark.parametrize("kind", ("forged", "delegating"))
def test_policy_method_replacement_denied_even_if_result_is_bound(
    monkeypatch, scope, kind,
):
    items = _inputs()
    registry, gate, call, _grants, backend = items
    original = PermissionGate.authorize_registered

    def fake(self, registry, call, grants, *, now_ms, one_shot=None):
        if kind == "forged":
            return registry.bind(call)
        return original(
            self, registry, call, grants, now_ms=now_ms, one_shot=one_shot,
        )

    if scope == "class":
        monkeypatch.setattr(PermissionGate, "authorize_registered", fake)
    else:
        monkeypatch.setattr(
            gate, "authorize_registered",
            lambda *args, **kwargs: fake(gate, *args, **kwargs),
        )
    with pytest.raises(
        DisconnectedReadPreflightRejected, match="policy implementation changed",
    ):
        _review(items)
    assert registry.bind(call).call is call
    assert gate._consumed_tokens == set()
    assert backend.calls == 0


@pytest.mark.parametrize("scope", ("class", "instance"))
def test_registry_callback_cannot_install_policy_forgery_mid_review(
    monkeypatch, scope,
):
    items = _inputs()
    registry, gate, call, _grants, backend = items
    original_bind = registry.bind

    def changed_bind(current):
        if scope == "class":
            monkeypatch.setattr(
                PermissionGate, "authorize_registered",
                lambda self, reg, c, grants, *, now_ms: reg.bind(c),
            )
        else:
            monkeypatch.setattr(
                gate, "authorize_registered",
                lambda reg, c, grants, *, now_ms: original_bind(c),
            )
        return original_bind(current)

    monkeypatch.setattr(registry, "bind", changed_bind)
    with pytest.raises(
        DisconnectedReadPreflightRejected, match="policy implementation changed",
    ):
        _review(items)
    assert gate._consumed_tokens == set()
    assert backend.calls == 0


def test_unmodified_read_policy_stays_tokenless_and_no_dispatch():
    items = _inputs()
    result = _review(items)
    assert result.backend_dispatched is False
    assert result.write_authorized is False
    assert result.durable_permission_proven is False
    assert items[1]._consumed_tokens == set()
    assert items[-1].calls == 0


@pytest.mark.parametrize("bad_gate", (None, object(), PermissionGate))
def test_invalid_gate_shape_rejected_as_bounded_input(bad_gate):
    registry, _gate, call, grants, backend = _inputs()
    with pytest.raises(
        DisconnectedReadPreflightRejected, match="exact bounded preflight inputs",
    ):
        review_disconnected_registered_read(
            registry, bad_gate, call, grants, now_ms=10,
        )
    assert backend.calls == 0
