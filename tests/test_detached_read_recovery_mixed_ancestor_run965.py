"""Run965: a terminal ancestor beats uncertainty in disconnected READ joins.

This is a pure in-memory mock-only graph. A locally SUCCEEDED receipt is not
verified execution, consent, a replay grant or a real ToolRegistry call.
"""

from __future__ import annotations

import pytest

from ark.agency.disconnected_read_recovery_schedule import (
    ReadRecoveryStep,
    schedule_detached_read_recovery,
)

_REQ = "req_" + "a" * 32
_A, _B, _C, _D, _E, _F = (
    "step_" + f"{digit}" * 16 for digit in "123456"
)
_STATES = ("FAILED", "UNKNOWN", "RUNNING", "NOT_STARTED", "SUCCEEDED")


def _step(name: str, state: str, deps: tuple[str, ...] = ()) -> ReadRecoveryStep:
    return ReadRecoveryStep(
        name, "math.sum", deps, state,
        "b" * 64 if state == "SUCCEEDED" else None,
    )


@pytest.mark.parametrize("first", _STATES)
@pytest.mark.parametrize("second", _STATES)
def test_mixed_ancestor_join_retains_strongest_blocker_and_independent_read(
    first: str, second: str,
) -> None:
    graph = (
        _step(_A, first),
        _step(_B, second),
        _step(_C, "NOT_STARTED", (_A, _B)),
        _step(_D, "NOT_STARTED", (_C,)),
        _step(_E, "SUCCEEDED"),
        _step(_F, "NOT_STARTED", (_E,)),
    )
    result = schedule_detached_read_recovery(_REQ, graph)
    decision = {item.step_id: item.disposition for item in result.decisions}
    if "FAILED" in (first, second):
        expected = "HOLD_FAILED"
    elif any(state in ("RUNNING", "UNKNOWN") for state in (first, second)):
        expected = "HOLD_UNCERTAIN"
    elif "NOT_STARTED" in (first, second):
        expected = "WAIT_DEPENDENCY"
    else:
        expected = "READY_MOCK_ONLY"
    assert decision[_C] == expected
    assert decision[_D] == (
        "WAIT_DEPENDENCY" if expected == "READY_MOCK_ONLY" else expected
    )
    assert decision[_E] == "COMPLETE_UNVERIFIED"
    assert decision[_F] == "READY_MOCK_ONLY"
    assert result == schedule_detached_read_recovery(_REQ, graph)
    assert len(result.schedule_digest) == 64
    assert result.dispatch_authorized is False
    assert result.automatic_replay_authorized is False
    assert result.external_outcome_verified is False
