"""Synthetic READ journal bridging must keep receipt identity after late getters."""

import pytest

import ark.agency.disconnected_read_receipt_bridge as bridge
from ark.agency.disconnected_fixture_binding import (
    DisconnectedFixtureBinding,
    bind_disconnected_fixture_result,
)
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


@pytest.mark.parametrize("field,bad", [
    ("request_id", "req_" + "f" * 32),
    ("step_id", "step_" + "f" * 16),
    ("operation", "text.stats"),
    ("input_digest", "f" * 64),
    ("result_digest", "f" * 64),
])
def test_late_denial_getter_cannot_retarget_read_receipt(
    monkeypatch, field, bad,
):
    req, res, binding = _case()
    original_receipt = bridge._RECEIPT_TYPE
    captured = []
    calls_after_receipt = 0

    def capture_receipt(*args):
        receipt = original_receipt(*args)
        captured.append(receipt)
        return receipt

    def mutating_denial_getter(self):
        nonlocal calls_after_receipt
        if captured:
            calls_after_receipt += 1
            # First late check validates normally, second mutates after it.
            if calls_after_receipt == 2:
                object.__setattr__(captured[0], field, bad)
        return False

    monkeypatch.setattr(bridge, "ReadReceipt", capture_receipt)
    monkeypatch.setattr(
        DisconnectedFixtureBinding, "dispatch_authorized",
        property(mutating_denial_getter),
    )
    with pytest.raises(
        bridge.DisconnectedReadBridgeRejected, match="receipt construction",
    ):
        bridge.prepare_disconnected_read_receipt(
            "step_" + "b" * 16, req, res, binding,
        )
    assert len(captured) == 1
    assert calls_after_receipt >= 2


def test_intact_read_receipt_has_exact_identity():
    req, res, binding = _case()
    receipt = bridge.prepare_disconnected_read_receipt(
        "step_" + "b" * 16, req, res, binding,
    )
    assert type(receipt) is bridge._RECEIPT_TYPE
    assert receipt.request_id == req.request_id
    assert receipt.operation == "math.sum"
    assert receipt.result_digest == res.result_digest
