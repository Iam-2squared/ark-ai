"""Disconnected READ bridge receipt and recomputed binding must stay exact."""

from __future__ import annotations

import pytest

import ark.agency.disconnected_read_receipt_bridge as bridge
from ark.agency.disconnected_fixture_binding import bind_disconnected_fixture_result
from ark.agency.disconnected_toolbox import (
    DisconnectedToolRequest,
    execute_disconnected_fixture_tool,
)


def _case():
    request = DisconnectedToolRequest(
        "req_" + "a" * 32, "math.sum", '{"values":[1,2]}',
    )
    result = execute_disconnected_fixture_tool(request)
    return request, result, bind_disconnected_fixture_result(request, result)


def test_replaced_read_receipt_class_is_rejected_even_if_values_look_valid(monkeypatch):
    request, result, binding = _case()

    executed = []

    class FakeReceipt:
        def __init__(self, request_id, step_id, operation, input_digest, result_digest):
            executed.append("forbidden constructor")
            raise AssertionError("replacement receipt must not be constructed")

    monkeypatch.setattr(bridge, "ReadReceipt", FakeReceipt)
    with pytest.raises(bridge.DisconnectedReadBridgeRejected, match="receipt descriptor"):
        bridge.prepare_disconnected_read_receipt(
            "step_" + "b" * 16, request, result, binding,
        )
    assert executed == []


@pytest.mark.parametrize(("field", "replacement"), [
    ("request_id", "req_" + "f" * 32),
    ("operation", "text.stats"),
    ("input_digest", "f" * 64),
    ("result_digest", "f" * 64),
    ("request_bound_digest", "f" * 64),
])
def test_substituted_receipt_factory_is_rejected_before_rebinding_or_construction(
    monkeypatch, field, replacement,
):
    request, result, binding = _case()
    original_binding = bridge.bind_disconnected_fixture_result
    original_receipt = bridge.ReadReceipt
    captured = []
    constructed = []

    def capture(req, res):
        verified = original_binding(req, res)
        captured.append(verified)
        return verified

    def mutate(*args, **kwargs):
        constructed.append((field, replacement))
        receipt = original_receipt(*args, **kwargs)
        object.__setattr__(captured[0], field, replacement)
        return receipt

    monkeypatch.setattr(bridge, "bind_disconnected_fixture_result", capture)
    monkeypatch.setattr(bridge, "ReadReceipt", mutate)
    with pytest.raises(bridge.DisconnectedReadBridgeRejected, match="receipt descriptor"):
        bridge.prepare_disconnected_read_receipt(
            "step_" + "b" * 16, request, result, binding,
        )
    assert captured == []
    assert constructed == []


def test_unmodified_bridge_still_builds_only_inert_read_row():
    request, result, binding = _case()
    receipt = bridge.prepare_disconnected_read_receipt(
        "step_" + "b" * 16, request, result, binding,
    )
    assert receipt.request_id == request.request_id
    assert receipt.step_id == "step_" + "b" * 16
    assert receipt.input_digest == result.input_digest
    assert receipt.result_digest == result.result_digest
    assert binding.dispatch_authorized is False
    assert binding.external_outcome_verified is False
    assert binding.automatic_replay_authorized is False
