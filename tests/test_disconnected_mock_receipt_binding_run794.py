"""Disconnected READ bridge rejects corrupted fixture receipts before digesting.

These tests inject a *faulty trusted test fixture*, not a real ToolBackend.
Changing the local expected callback is test instrumentation ONLY; it does not
show code provenance, actual permission, consent or external execution.
"""

from __future__ import annotations

from dataclasses import replace

import pytest

from ark.agency import disconnected_read_tool_bridge as bridge

_REQUEST = "req_" + "a" * 32
_FIRST = "step_" + "1" * 16
_SECOND = "step_" + "2" * 16


def _inputs():
    steps = (
        bridge.recovery.ReadRecoveryStep(
            _FIRST, "math.sum", (), "NOT_STARTED", None,
        ),
        bridge.recovery.ReadRecoveryStep(
            _SECOND, "text.find", (), "NOT_STARTED", None,
        ),
    )
    requests = (
        bridge.fixture.DisconnectedToolRequest(
            bridge.derive_disconnected_read_fixture_id(_REQUEST, _FIRST),
            "math.sum", '{"values":[4,6]}',
        ),
        bridge.fixture.DisconnectedToolRequest(
            bridge.derive_disconnected_read_fixture_id(_REQUEST, _SECOND),
            "text.find", '{"needle":"abc","text":"zabc"}',
        ),
    )
    bindings = tuple(
        bridge.DetachedReadToolBinding(step, request)
        for step, request in zip((_FIRST, _SECOND), requests, strict=True)
    )
    return steps, bindings


def test_two_independent_valid_receipts_have_stable_mock_manifest():
    steps, bindings = _inputs()
    first = bridge.preview_disconnected_read_tools(_REQUEST, steps, bindings)
    again = bridge.preview_disconnected_read_tools(_REQUEST, steps, bindings)
    assert first == again
    assert first.ready_step_ids == (_FIRST, _SECOND)
    assert first.withheld_step_ids == ()
    assert first.fixture_results[0].canonical_result_json == '{"count":2,"sum":10}'
    assert first.fixture_results[1].canonical_result_json == '{"index":1}'
    assert len(first.fingerprint) == 64
    assert first.dispatch_authorized is False
    assert first.automatic_replay_authorized is False


@pytest.mark.parametrize("tamper", (
    "input_digest", "result_digest", "request_id", "operation",
    "result_content", "noncanonical_json", "huge_result", "non_str",
))
def test_faulty_fixture_receipt_cannot_enter_preview_fingerprint(
    monkeypatch: pytest.MonkeyPatch, tamper: str,
):
    steps, bindings = _inputs()
    original = bridge.fixture.execute_disconnected_fixture_tool
    triggered = []

    def faulty(request: bridge.fixture.DisconnectedToolRequest):
        correct = original(request)
        if request.request_id != bindings[0].request.request_id:
            return correct
        triggered.append(tamper)
        if tamper == "input_digest":
            return replace(correct, input_digest="0" * 64)
        if tamper == "result_digest":
            return replace(correct, result_digest="0" * 64)
        if tamper == "request_id":
            return replace(correct, request_id="req_" + "f" * 32)
        if tamper == "operation":
            return replace(correct, operation="text.stats")
        if tamper == "result_content":
            return replace(correct, canonical_result_json='{"count":1,"sum":10}')
        if tamper == "noncanonical_json":
            return replace(correct, canonical_result_json='{"sum":10, "count":2}')
        if tamper == "huge_result":
            return replace(correct, canonical_result_json="x" * 16_385)
        return replace(correct, result_digest=None)

    # Explicitly simulate an implementation bug inside the otherwise pinned
    # disconnected executor. This is NOT a production permission bypass.
    with monkeypatch.context() as patch:
        patch.setattr(bridge.fixture, "execute_disconnected_fixture_tool", faulty)
        patch.setattr(bridge, "_ORIGINAL_EXECUTE", faulty)
        with pytest.raises(bridge.DisconnectedReadToolBridgeRejected):
            bridge.preview_disconnected_read_tools(_REQUEST, steps, bindings)
    assert triggered == [tamper]
