"""Run546: registered READ rechecks retain denial descriptors to the end."""

from __future__ import annotations

import pytest

from ark.agency import disconnected_registered_read_recheck as mod
from ark.agency.contracts import CapabilityGrant, Effect, ToolCall
from ark.agency.disconnected_registered_read_preflight import (
    DisconnectedReadPreflight,
    review_disconnected_registered_read,
)
from ark.agency.policy import PermissionGate
from ark.agency.registry import ToolRegistration, ToolRegistry


class NoDispatch:
    def __init__(self):
        self.calls = 0

    def execute(self, _call):
        self.calls += 1
        raise AssertionError("registered READ review dispatched a real backend")


def _fixture():
    backend = NoDispatch()
    registry = ToolRegistry((
        ToolRegistration(
            "local.inspect", "local.inspect", Effect.READ,
            "mock:01", backend,
        ),
    ))
    gate = PermissionGate()
    call = ToolCall("local.inspect", "local.inspect", "fixture:user", {"x": 1})
    grants = (CapabilityGrant("local.inspect", "fixture:user", 200),)
    receipt = review_disconnected_registered_read(
        registry, gate, call, grants, now_ms=100,
    )
    return registry, gate, call, grants, receipt, backend


def _verify(values):
    registry, gate, call, grants, receipt, _backend = values
    return mod.verify_disconnected_registered_read_receipt(
        receipt, registry, gate, call, grants, now_ms=100,
    )


def test_registered_read_recheck_remains_inert_and_authority_free():
    values = _fixture()
    assert _verify(values) is None
    assert values[-1].calls == 0


@pytest.mark.parametrize("replaced", (
    "backend_dispatched",
    "external_read_authorized",
))
def test_false_receipt_getter_cannot_rebind_equal_denial_descriptor(
    monkeypatch, replaced,
):
    values = _fixture()
    receipt = values[4]

    def malicious(self):
        if self is receipt:
            monkeypatch.setattr(
                DisconnectedReadPreflight, replaced,
                property(lambda _record: False),
            )
        return False

    monkeypatch.setattr(
        DisconnectedReadPreflight, "durable_permission_proven",
        property(malicious),
    )
    with pytest.raises(mod.DisconnectedReadReceiptRejected, match="epoch changed"):
        _verify(values)
    assert values[-1].calls == 0


def test_fresh_last_denial_cannot_grant_permission_on_final_check(monkeypatch):
    values = _fixture()
    original = mod.review_disconnected_registered_read
    fresh = []
    checks = [0]

    def wrapped(*args, **kwargs):
        result = original(*args, **kwargs)
        fresh.append(result)
        return result

    def malicious(self):
        if fresh and self is fresh[0]:
            checks[0] += 1
            if checks[0] == 2:
                monkeypatch.setattr(
                    DisconnectedReadPreflight, "backend_dispatched",
                    property(lambda _record: True),
                )
        return False

    monkeypatch.setattr(mod, "review_disconnected_registered_read", wrapped)
    monkeypatch.setattr(
        DisconnectedReadPreflight, "durable_permission_proven",
        property(malicious),
    )
    # The registered preflight now rejects the preinstalled False-looking
    # denial descriptor before constructing a fresh receipt. This earlier
    # denial is stronger than allowing the malicious second callback to run.
    with pytest.raises(
        mod.DisconnectedReadReceiptRejected, match="fresh registry READ review denied",
    ):
        _verify(values)
    assert checks[0] == 0
    assert values[-1].calls == 0


def test_fresh_callback_cannot_swap_equal_denial_descriptor(monkeypatch):
    values = _fixture()
    original = mod.review_disconnected_registered_read

    def wrapped(*args, **kwargs):
        result = original(*args, **kwargs)
        monkeypatch.setattr(
            DisconnectedReadPreflight, "write_authorized",
            property(lambda _record: False),
        )
        return result

    monkeypatch.setattr(mod, "review_disconnected_registered_read", wrapped)
    with pytest.raises(mod.DisconnectedReadReceiptRejected, match="epoch changed"):
        _verify(values)
    assert values[-1].calls == 0
