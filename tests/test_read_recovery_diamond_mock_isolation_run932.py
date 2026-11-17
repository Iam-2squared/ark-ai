"""Disconnected READ fan-in recovery remains mock-only under mixed outcomes.

A successful predecessor is only caller-asserted, not authenticated evidence.
No ToolBackend, account, filesystem mutation, network or live tool is touched.
"""

from __future__ import annotations

import pytest

from ark.agency import disconnected_read_tool_bridge as bridge

_REQUEST = "req_" + "9" * 32
_ONE = "step_" + "1" * 16
_TWO = "step_" + "2" * 16
_THREE = "step_" + "3" * 16
_FOUR = "step_" + "4" * 16
_FIVE = "step_" + "5" * 16
_DIGEST = "a" * 64


def _step(identifier: str, *, depends_on=(), state="NOT_STARTED"):
    return bridge.recovery.ReadRecoveryStep(
        identifier, "math.sum", depends_on, state,
        _DIGEST if state == "SUCCEEDED" else None,
    )


def _binding(identifier: str, *, values="[3,4]"):
    request = bridge.fixture.DisconnectedToolRequest(
        bridge.derive_disconnected_read_fixture_id(_REQUEST, identifier),
        "math.sum", '{"values":' + values + "}",
    )
    return bridge.DetachedReadToolBinding(identifier, request)


@pytest.mark.parametrize(
    ("first_state", "expected_join", "ready"),
    (
        ("UNKNOWN", "HOLD_UNCERTAIN", (_FOUR,)),
        ("RUNNING", "HOLD_UNCERTAIN", (_FOUR,)),
        ("FAILED", "HOLD_FAILED", (_FOUR,)),
        ("NOT_STARTED", "WAIT_DEPENDENCY", (_ONE, _FOUR)),
        ("SUCCEEDED", "READY_MOCK_ONLY", (_THREE, _FOUR)),
    ),
)
def test_mixed_fan_in_quarantine_and_unrelated_mock_isolation(
    first_state: str, expected_join: str, ready: tuple[str, ...],
) -> None:
    # _THREE joins two predecessors, _FIVE depends on that join, and
    # _FOUR is unrelated. Order is a topological order, not a retry queue.
    steps = (
        _step(_ONE, state=first_state),
        _step(_TWO, state="SUCCEEDED"),
        _step(_THREE, depends_on=(_ONE, _TWO)),
        _step(_FOUR),
        _step(_FIVE, depends_on=(_THREE,)),
    )
    schedule = bridge.recovery.schedule_detached_read_recovery(_REQUEST, steps)
    assert schedule.decisions[2].disposition == expected_join
    assert schedule.decisions[4].disposition == (
        "HOLD_UNCERTAIN" if first_state in ("UNKNOWN", "RUNNING")
        else "HOLD_FAILED" if first_state == "FAILED"
        else "WAIT_DEPENDENCY"
    )
    bindings = tuple(_binding(identifier) for identifier in ready)
    first = bridge.preview_disconnected_read_tools(_REQUEST, steps, bindings)
    second = bridge.preview_disconnected_read_tools(_REQUEST, steps, bindings)
    assert first == second
    assert first.ready_step_ids == ready
    assert first.withheld_step_ids == tuple(
        identifier for identifier in (_ONE, _TWO, _THREE, _FOUR, _FIVE)
        if identifier not in ready
    )
    assert tuple(
        result.canonical_result_json for result in first.fixture_results
    ) == ('{"count":2,"sum":7}',) * len(ready)
    assert all(
        result.dispatch_authorized is False
        and result.automatic_replay_authorized is False
        and result.external_outcome_known is False
        for result in first.fixture_results
    )
    assert first.dispatch_authorized is False
    assert first.automatic_replay_authorized is False
    assert first.external_effect_verified is False
    assert first.consent_authenticated is False


@pytest.mark.parametrize("first_state", ("UNKNOWN", "RUNNING", "FAILED"))
def test_fan_in_held_step_cannot_be_bound_to_mock(
    first_state: str,
) -> None:
    steps = (
        _step(_ONE, state=first_state),
        _step(_TWO, state="SUCCEEDED"),
        _step(_THREE, depends_on=(_ONE, _TWO)),
        _step(_FOUR),
    )
    # Even though the unrelated fourth step may run as an inert calculation,
    # including a dependency-contaminated third step must reject the whole
    # binding set rather than silently execute it or drop it.
    with pytest.raises(bridge.DisconnectedReadToolBridgeRejected):
        bridge.preview_disconnected_read_tools(
            _REQUEST, steps, (_binding(_THREE), _binding(_FOUR)),
        )


@pytest.mark.parametrize("values", ("[3,4]", "[3,5]", "[4,3]"))
def test_mock_input_change_is_bound_to_derived_preview_fingerprint(
    values: str,
) -> None:
    steps = (_step(_ONE),)
    baseline = bridge.preview_disconnected_read_tools(
        _REQUEST, steps, (_binding(_ONE),),
    )
    altered = bridge.preview_disconnected_read_tools(
        _REQUEST, steps, (_binding(_ONE, values=values),),
    )
    assert baseline.schedule_digest == altered.schedule_digest
    if values == "[3,4]":
        assert baseline == altered
    else:
        assert baseline.fingerprint != altered.fingerprint
        assert (
            baseline.fixture_results[0].input_digest
            != altered.fixture_results[0].input_digest
        )
    assert altered.automatic_replay_authorized is False
