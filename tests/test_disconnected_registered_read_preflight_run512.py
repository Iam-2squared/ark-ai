"""Zero-dispatch registered READ-only preflight integration tests."""

from __future__ import annotations

from dataclasses import FrozenInstanceError

import pytest

from ark.agency.contracts import CapabilityGrant, Effect, ToolCall
from ark.agency.disconnected_registered_read_preflight import (
    DisconnectedReadPreflight,
    DisconnectedReadPreflightRejected,
    review_disconnected_registered_read,
)
from ark.agency.policy import PermissionGate
from ark.agency.registry import ToolRegistration, ToolRegistry


class _NoDispatchBackend:
    def __init__(self) -> None:
        self.calls = 0

    def execute(self, call: ToolCall) -> object:
        self.calls += 1
        raise AssertionError("a disconnected preflight must not execute a backend")


def _make(effect: Effect = Effect.READ):
    backend = _NoDispatchBackend()
    registry = ToolRegistry((
        ToolRegistration("files.inspect", "files.inspect", effect, "fixture:1", backend),
    ))
    call = ToolCall(
        "files.inspect", "files.inspect", "workspace:fixture",
        {"path": "private-contents.txt"},
    )
    gate = PermissionGate()
    grant = CapabilityGrant("files.inspect", "workspace:fixture", 100)
    return registry, gate, call, grant, backend


def test_registered_read_is_inert_and_bound_to_registry() -> None:
    registry, gate, call, grant, backend = _make()
    report = review_disconnected_registered_read(
        registry, gate, call, (grant,), now_ms=50,
    )
    assert type(report) is DisconnectedReadPreflight
    assert report.registry_revision == registry.revision
    assert report.bound_action_id == registry.bind(call).bound_action_id
    assert report.request_id == call.request_id
    assert report.tool_name == "files.inspect"
    assert report.capability == "files.inspect"
    assert not any((
        report.backend_dispatched, report.external_read_authorized,
        report.write_authorized, report.trusted_clock_verified,
        report.durable_permission_proven,
    ))
    assert backend.calls == 0
    assert "private-contents.txt" not in repr(report)
    assert gate._consumed_tokens == set()


def test_read_review_is_repeatable_without_spending_token() -> None:
    registry, gate, call, grant, backend = _make()
    one = review_disconnected_registered_read(registry, gate, call, (grant,), now_ms=4)
    two = review_disconnected_registered_read(registry, gate, call, (grant,), now_ms=4)
    assert one == two
    assert backend.calls == 0
    assert not gate._consumed_tokens


def test_registered_write_denied_before_permission_gate() -> None:
    registry, gate, call, grant, backend = _make(Effect.WRITE)
    with pytest.raises(DisconnectedReadPreflightRejected, match="non-READ"):
        review_disconnected_registered_read(registry, gate, call, (grant,), now_ms=50)
    assert not gate._consumed_tokens
    assert backend.calls == 0


@pytest.mark.parametrize(
    "mode",
    ("no_grant", "wrong_scope", "wrong_capability", "expired", "at_expiry"),
)
def test_exact_scope_expiry_and_missing_grants_denied(mode: str) -> None:
    registry, gate, call, grant, backend = _make()
    claims = {
        "no_grant": (),
        "wrong_scope": (CapabilityGrant("files.inspect", "workspace:other"),),
        "wrong_capability": (CapabilityGrant("other", "workspace:fixture"),),
        "expired": (CapabilityGrant("files.inspect", "workspace:fixture", 1),),
        "at_expiry": (grant,),
    }
    with pytest.raises(DisconnectedReadPreflightRejected, match="denied"):
        review_disconnected_registered_read(
            registry, gate, call, claims[mode], now_ms=100,
        )
    assert backend.calls == 0


@pytest.mark.parametrize("now", (True, -1, 2**63, 1.0, "50"))
def test_synthetic_clock_requires_exact_bounded_integer(now: object) -> None:
    registry, gate, call, grant, backend = _make()
    with pytest.raises(DisconnectedReadPreflightRejected, match="exact bounded"):
        review_disconnected_registered_read(
            registry, gate, call, (grant,), now_ms=now,
        )
    assert backend.calls == 0


def test_grant_container_must_be_exact_tuple_and_bounded() -> None:
    registry, gate, call, grant, backend = _make()
    for grants in ([grant], tuple([grant] * 129), (object(),)):
        with pytest.raises(DisconnectedReadPreflightRejected, match="exact bounded"):
            review_disconnected_registered_read(
                registry, gate, call, grants, now_ms=1,
            )
    assert backend.calls == 0


def test_unknown_tool_or_spoofed_capability_is_denied() -> None:
    registry, gate, _, grant, backend = _make()
    for call in (
        ToolCall("unknown", "files.inspect", "workspace:fixture"),
        ToolCall("files.inspect", "other", "workspace:fixture"),
    ):
        with pytest.raises(DisconnectedReadPreflightRejected, match="denied"):
            review_disconnected_registered_read(
                registry, gate, call, (grant,), now_ms=1,
            )
    assert backend.calls == 0


def test_reflected_grant_change_during_policy_check_is_denied(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    registry, gate, call, grant, backend = _make()
    original = PermissionGate.authorize_registered

    def mutating(self, reg, action, claims, *, now_ms, one_shot=None):
        object.__setattr__(grant, "scope", "workspace:changed")
        return original(self, reg, action, claims, now_ms=now_ms, one_shot=one_shot)

    monkeypatch.setattr(PermissionGate, "authorize_registered", mutating)
    with pytest.raises(
        DisconnectedReadPreflightRejected, match="policy implementation changed",
    ):
        review_disconnected_registered_read(registry, gate, call, (grant,), now_ms=1)
    assert backend.calls == 0


def test_substituted_policy_return_cannot_pass_binding_check(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    registry, gate, call, grant, backend = _make()

    def substitute(self, reg, action, claims, *, now_ms, one_shot=None):
        return object()

    monkeypatch.setattr(PermissionGate, "authorize_registered", substitute)
    with pytest.raises(
        DisconnectedReadPreflightRejected, match="policy implementation changed",
    ):
        review_disconnected_registered_read(registry, gate, call, (grant,), now_ms=1)
    assert backend.calls == 0


def test_report_is_frozen_and_denials_are_not_dispatch(monkeypatch) -> None:
    registry, gate, call, grant, backend = _make()
    report = review_disconnected_registered_read(
        registry, gate, call, (grant,), now_ms=1,
    )
    with pytest.raises((FrozenInstanceError, TypeError)):
        report.write_authorized = True
    assert backend.calls == 0


def test_equal_value_replaced_call_scope_is_not_the_original_epoch(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    registry, gate, call, grant, backend = _make()

    def replace_scope(self, reg, action, claims, *, now_ms, one_shot=None):
        replacement = (" " + call.scope)[1:]
        assert replacement == call.scope and replacement is not call.scope
        object.__setattr__(call, "scope", replacement)
        return reg.bind(action)

    monkeypatch.setattr(PermissionGate, "authorize_registered", replace_scope)
    with pytest.raises(
        DisconnectedReadPreflightRejected, match="policy implementation changed",
    ):
        review_disconnected_registered_read(registry, gate, call, (grant,), now_ms=1)
    assert backend.calls == 0
