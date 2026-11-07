"""Late authority getters cannot rewrite detached READ receipt identities."""

from __future__ import annotations

from dataclasses import replace

import pytest

import ark.agency.disconnected_registered_read_preflight as preflight
import ark.agency.disconnected_registered_read_recheck as recheck
from ark.agency.contracts import CapabilityGrant, Effect, ToolCall
from ark.agency.policy import PermissionGate
from ark.agency.registry import ToolRegistration, ToolRegistry


class _NoDispatchBackend:
    def __init__(self):
        self.calls = 0

    def execute(self, call):
        self.calls += 1
        raise AssertionError("disconnected receipt checks may not dispatch")


def _fixture():
    backend = _NoDispatchBackend()
    registry = ToolRegistry((
        ToolRegistration("local.inspect", "local.inspect", Effect.READ, "mock:1", backend),
    ))
    gate = PermissionGate()
    call = ToolCall("local.inspect", "local.inspect", "workspace:test", {"key": "private"})
    grant = CapabilityGrant("local.inspect", "workspace:test", 200)
    return registry, gate, call, grant, backend


def _receipt(registry, gate, call, grant):
    return preflight.review_disconnected_registered_read(
        registry, gate, call, (grant,), now_ms=100,
    )


def test_benign_preflight_and_retained_recheck_remain_noops():
    registry, gate, call, grant, backend = _fixture()
    receipt = _receipt(registry, gate, call, grant)
    assert recheck.verify_disconnected_registered_read_receipt(
        receipt, registry, gate, call, (grant,), now_ms=100,
    ) is None
    assert backend.calls == 0
    assert gate._consumed_tokens == set()
    assert "private" not in repr(receipt)


@pytest.mark.parametrize("field", (
    "registry_revision", "bound_action_id", "request_id", "tool_name", "capability",
))
def test_final_preflight_denial_getter_cannot_replace_field(
    monkeypatch, field,
):
    registry, gate, call, grant, backend = _fixture()

    def late_change(self):
        object.__setattr__(self, field, "forged-after-field-check")
        return False

    monkeypatch.setattr(
        preflight.DisconnectedReadPreflight,
        "durable_permission_proven",
        property(late_change),
    )
    with pytest.raises(preflight.DisconnectedReadPreflightRejected, match="authority"):
        _receipt(registry, gate, call, grant)
    assert backend.calls == 0
    assert not gate._consumed_tokens


@pytest.mark.parametrize("field", (
    "registry_revision", "bound_action_id", "request_id", "tool_name", "capability",
))
def test_fresh_recheck_denial_getter_cannot_swap_equal_type_field(
    monkeypatch, field,
):
    registry, gate, call, grant, backend = _fixture()
    retained = _receipt(registry, gate, call, grant)
    expected = replace(retained)
    monkeypatch.setattr(
        recheck, "review_disconnected_registered_read",
        lambda *args, **kwargs: expected,
    )

    def late_change(self):
        if self is expected:
            original = getattr(self, field)
            replacement = (" " + original)[1:]
            assert replacement == original and replacement is not original
            object.__setattr__(self, field, replacement)
        return False

    monkeypatch.setattr(
        preflight.DisconnectedReadPreflight,
        "durable_permission_proven",
        property(late_change),
    )
    with pytest.raises(recheck.DisconnectedReadReceiptRejected, match="differs"):
        recheck.verify_disconnected_registered_read_receipt(
            retained, registry, gate, call, (grant,), now_ms=100,
        )
    assert backend.calls == 0
    assert not gate._consumed_tokens


def test_last_retained_receipt_denial_getter_cannot_retarget_grant(
    monkeypatch,
):
    registry, gate, call, grant, backend = _fixture()
    receipt = _receipt(registry, gate, call, grant)

    def late_change(self):
        if self is receipt:
            other = (" " + grant.scope)[1:]
            assert other == grant.scope and other is not grant.scope
            object.__setattr__(grant, "scope", other)
        return False

    monkeypatch.setattr(
        preflight.DisconnectedReadPreflight,
        "durable_permission_proven",
        property(late_change),
    )
    with pytest.raises(recheck.DisconnectedReadReceiptRejected, match="epoch changed"):
        recheck.verify_disconnected_registered_read_receipt(
            receipt, registry, gate, call, (grant,), now_ms=100,
        )
    assert backend.calls == 0
    assert not gate._consumed_tokens


def test_last_retained_receipt_denial_getter_cannot_swap_equal_value_id(
    monkeypatch,
):
    registry, gate, call, grant, backend = _fixture()
    receipt = _receipt(registry, gate, call, grant)

    def late_change(self):
        if self is receipt:
            original = self.bound_action_id
            other = (" " + original)[1:]
            assert other == original and other is not original
            object.__setattr__(self, "bound_action_id", other)
        return False

    monkeypatch.setattr(
        preflight.DisconnectedReadPreflight,
        "durable_permission_proven",
        property(late_change),
    )
    with pytest.raises(recheck.DisconnectedReadReceiptRejected, match="epoch changed"):
        recheck.verify_disconnected_registered_read_receipt(
            receipt, registry, gate, call, (grant,), now_ms=100,
        )
    assert backend.calls == 0
    assert not gate._consumed_tokens


def test_original_authority_flip_still_fails_closed(monkeypatch):
    registry, gate, call, grant, backend = _fixture()
    receipt = _receipt(registry, gate, call, grant)
    monkeypatch.setattr(
        preflight.DisconnectedReadPreflight,
        "durable_permission_proven", property(lambda self: True),
    )
    with pytest.raises(recheck.DisconnectedReadReceiptRejected):
        recheck.verify_disconnected_registered_read_receipt(
            receipt, registry, gate, call, (grant,), now_ms=100,
        )
    assert backend.calls == 0
