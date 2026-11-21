"""Retained synthetic READ recheck rejects substituted receipt accessors before use.

Class slots and false-returning denial getters are process-local callback
surfaces, not evidence of trusted authorization. No real backend is dispatched.
"""

from __future__ import annotations

import pytest

from ark.agency.contracts import CapabilityGrant, Effect, ToolCall
from ark.agency.disconnected_registered_read_preflight import (
    DisconnectedReadPreflight,
    review_disconnected_registered_read,
)
from ark.agency.disconnected_registered_read_recheck import (
    DisconnectedReadReceiptRejected,
    verify_disconnected_registered_read_receipt,
)
from ark.agency.policy import PermissionGate
from ark.agency.registry import ToolRegistration, ToolRegistry


class _InertBackend:
    def __init__(self) -> None:
        self.calls = 0

    def execute(self, _call: ToolCall) -> None:
        self.calls += 1
        raise AssertionError("retained READ inspection dispatched a backend")


def _fixture():
    backend = _InertBackend()
    registry = ToolRegistry((
        ToolRegistration(
            "fixture.read", "fixture.read", Effect.READ, "offline:read:v1", backend,
        ),
    ))
    gate = PermissionGate()
    call = ToolCall("fixture.read", "fixture.read", "fixture:owner", {"n": 1})
    grants = (CapabilityGrant("fixture.read", "fixture:owner", 500),)
    receipt = review_disconnected_registered_read(
        registry, gate, call, grants, now_ms=100,
    )
    return registry, gate, call, grants, receipt, backend


def _recheck(values):
    registry, gate, call, grants, receipt, _backend = values
    return verify_disconnected_registered_read_receipt(
        receipt, registry, gate, call, grants, now_ms=100,
    )


@pytest.mark.parametrize(
    "field",
    ("registry_revision", "bound_action_id", "request_id", "tool_name", "capability"),
)
def test_replaced_receipt_field_slot_is_rejected_before_getter(
    monkeypatch: pytest.MonkeyPatch, field: str,
) -> None:
    values = _fixture()
    touched = []

    def hostile(_self):
        touched.append(field)
        return "counterfeit"

    monkeypatch.setattr(DisconnectedReadPreflight, field, property(hostile))
    with pytest.raises(DisconnectedReadReceiptRejected, match="epoch changed"):
        _recheck(values)
    assert touched == []
    assert values[-1].calls == 0
    assert values[1]._consumed_tokens == set()


@pytest.mark.parametrize(
    "flag",
    (
        "backend_dispatched", "external_read_authorized", "write_authorized",
        "trusted_clock_verified", "durable_permission_proven",
    ),
)
def test_replaced_false_denial_property_is_rejected_before_getter(
    monkeypatch: pytest.MonkeyPatch, flag: str,
) -> None:
    values = _fixture()
    touched = []

    def fake(_self):
        touched.append(flag)
        return False

    monkeypatch.setattr(DisconnectedReadPreflight, flag, property(fake))
    with pytest.raises(DisconnectedReadReceiptRejected, match="epoch changed"):
        _recheck(values)
    assert touched == []
    assert values[-1].calls == 0


def test_replaced_class_lookup_hook_cannot_inspect_private_receipt(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    values = _fixture()
    touched = []

    def hostile(self, name):
        touched.append(name)
        return object.__getattribute__(self, name)

    monkeypatch.setattr(DisconnectedReadPreflight, "__getattribute__", hostile)
    with pytest.raises(DisconnectedReadReceiptRejected, match="epoch changed"):
        _recheck(values)
    assert touched == []
    assert values[-1].calls == 0


def test_original_retained_receipt_check_is_tokenless_and_inert() -> None:
    values = _fixture()
    assert _recheck(values) is None
    assert values[-1].calls == 0
    assert values[1]._consumed_tokens == set()
