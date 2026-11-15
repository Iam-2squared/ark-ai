"""Inert READ fixtures cannot be silently retargeted in bridge callbacks.

Only deterministic in-memory synthetic JSON and recovery fixtures are used;
no ToolBackend, external action, real approval or private context is accessed.
"""

from __future__ import annotations

import pytest

from ark.agency import disconnected_read_tool_bridge as bridge

_REQUEST = "req_" + "a" * 32
_STEP = "step_" + "1" * 16


def _inputs():
    tool_request = bridge.fixture.DisconnectedToolRequest(
        bridge.derive_disconnected_read_fixture_id(_REQUEST, _STEP),
        "math.sum", '{"values":[2,3]}',
    )
    step = bridge.recovery.ReadRecoveryStep(
        _STEP, "math.sum", (), "NOT_STARTED", None,
    )
    return (step,), (bridge.DetachedReadToolBinding(_STEP, tool_request),), tool_request


@pytest.mark.parametrize("attack", ("args", "equal-id"))
def test_mutated_request_during_identity_callback_cannot_run_mock(
    monkeypatch: pytest.MonkeyPatch, attack: str,
) -> None:
    steps, bindings, request = _inputs()
    derive = bridge.derive_disconnected_read_fixture_id
    original_id = request.request_id
    calls = []

    def mutate_after_check(request_id: str, step_id: str) -> str:
        calls.append(1)
        if attack == "args":
            object.__setattr__(request, "canonical_args_json", '{"values":[30,40]}')
        else:
            cloned = "".join((original_id[:4], original_id[4:]))
            assert cloned == original_id and cloned is not original_id
            object.__setattr__(request, "request_id", cloned)
        return derive(request_id, step_id)

    with monkeypatch.context() as patch:
        patch.setattr(bridge, "derive_disconnected_read_fixture_id", mutate_after_check)
        with pytest.raises(
            bridge.DisconnectedReadToolBridgeRejected, match="bridge input changed",
        ):
            bridge.preview_disconnected_read_tools(_REQUEST, steps, bindings)

    assert calls == [1]
    assert bindings[0].request is request


def test_rebound_tool_request_slot_cannot_execute_descriptor(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    steps, bindings, _request = _inputs()
    called = []

    def forbidden(_self: object) -> str:
        called.append(True)
        raise AssertionError("private args descriptor executed")

    with monkeypatch.context() as patch:
        patch.setattr(
            bridge.fixture.DisconnectedToolRequest,
            "canonical_args_json",
            property(forbidden),
        )
        with pytest.raises(
            (bridge.DisconnectedReadToolBridgeRejected, bridge.fixture.DisconnectedToolRejected),
        ):
            bridge.preview_disconnected_read_tools(_REQUEST, steps, bindings)

    assert called == []


def test_unmodified_disconnected_read_still_has_no_authority() -> None:
    steps, bindings, _request = _inputs()
    result = bridge.preview_disconnected_read_tools(_REQUEST, steps, bindings)
    assert result.ready_step_ids == (_STEP,)
    assert result.fixture_results[0].canonical_result_json == '{"count":2,"sum":5}'
    assert result.dispatch_authorized is False
    assert result.automatic_replay_authorized is False
    assert result.consent_authenticated is False
