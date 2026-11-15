"""Mock READ bridge must refuse replaced receipt result descriptors preaccess.

All fixtures are deterministic in-memory inputs. No backend dispatch, real
permission, external I/O, user data or automatic replay is involved.
"""

import pytest

from ark.agency import disconnected_read_tool_bridge as bridge

_REQUEST = "req_" + "a" * 32
_STEP = "step_" + "1" * 16


def _inputs():
    request = bridge.fixture.DisconnectedToolRequest(
        bridge.derive_disconnected_read_fixture_id(_REQUEST, _STEP),
        "math.sum", '{"values":[2,3]}',
    )
    steps = (bridge.recovery.ReadRecoveryStep(
        _STEP, "math.sum", (), "NOT_STARTED", None,
    ),)
    return steps, (bridge.DetachedReadToolBinding(_STEP, request),)


@pytest.mark.parametrize(
    "name",
    (
        "request_id",
        "operation",
        "input_digest",
        "canonical_result_json",
        "result_digest",
        "dispatch_authorized",
        "automatic_replay_authorized",
        "external_outcome_known",
    ),
)
def test_replaced_mock_result_descriptor_denied_before_getter(
    monkeypatch: pytest.MonkeyPatch, name: str,
) -> None:
    steps, bindings = _inputs()
    touched = []

    def forbidden(_self: object) -> object:
        touched.append(name)
        raise AssertionError("untrusted mock receipt descriptor executed")

    with monkeypatch.context() as patch:
        patch.setattr(
            bridge.fixture.DisconnectedToolResult,
            name, property(forbidden),
        )
        with pytest.raises(
            bridge.DisconnectedReadToolBridgeRejected,
            match="mock fixture result descriptor changed",
        ):
            bridge.preview_disconnected_read_tools(_REQUEST, steps, bindings)
    assert touched == []


def test_replaced_result_guard_is_never_called(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    steps, bindings = _inputs()
    touched = []

    def forbidden() -> None:
        touched.append("guard")
        raise AssertionError("untrusted result validator executed")

    with monkeypatch.context() as patch:
        patch.setattr(
            bridge.fixture, "_require_original_result_denials", forbidden,
        )
        with pytest.raises(
            bridge.DisconnectedReadToolBridgeRejected, match="mock bridge protocol changed",
        ):
            bridge.preview_disconnected_read_tools(_REQUEST, steps, bindings)
    assert touched == []


def test_original_receipt_still_has_no_execution_or_replay_authority() -> None:
    steps, bindings = _inputs()
    result = bridge.preview_disconnected_read_tools(_REQUEST, steps, bindings)
    assert result.ready_step_ids == (_STEP,)
    assert result.fixture_results[0].canonical_result_json == '{"count":2,"sum":5}'
    assert result.dispatch_authorized is False
    assert result.automatic_replay_authorized is False
    assert result.external_effect_verified is False
    assert result.consent_authenticated is False
