"""Finite-state reference check of conservative detached READ recovery.

The independent oracle enumerates complete small DAG state images rather
than checking only hand-selected fixtures. It never dispatches a tool or
treats READY_MOCK_ONLY/COMPLETE_UNVERIFIED as authorization.
"""

from __future__ import annotations

from itertools import product

import pytest

from ark.agency.disconnected_read_recovery_schedule import (
    DetachedReadRecoveryRejected,
    ReadRecoveryStep,
    schedule_detached_read_recovery,
)

_REQUEST = "req_" + "e" * 32
_NAMES = tuple("step_" + char * 16 for char in "1234")
_STATES = ("NOT_STARTED", "SUCCEEDED", "FAILED", "RUNNING", "UNKNOWN")
_SHAPES = (
    ((), (0,), (1,), (2,)),        # four-node linear chain
    ((), (0,), (0,), (1, 2)),      # diamond fan-in
    ((), (), (0,), (1, 2)),        # independent root, joined tail
    ((), (), (0, 1), (0, 2)),      # shared root with sibling tails
)


def _reference(states, shape):
    """Independently compute diagnostics or reject impossible started states."""
    decisions = []
    for state, parents in zip(states, shape, strict=True):
        if state != "NOT_STARTED" and any(
            states[parent] != "SUCCEEDED" for parent in parents
        ):
            return None
        parents_codes = tuple(decisions[parent] for parent in parents)
        if state == "SUCCEEDED":
            code = "COMPLETE_UNVERIFIED"
        elif state == "FAILED":
            code = "TERMINAL_FAILURE"
        elif state in ("RUNNING", "UNKNOWN"):
            code = "QUARANTINE_UNCERTAIN"
        elif any(code in ("TERMINAL_FAILURE", "HOLD_FAILED") for code in parents_codes):
            code = "HOLD_FAILED"
        elif any(
            code in ("QUARANTINE_UNCERTAIN", "HOLD_UNCERTAIN")
            for code in parents_codes
        ):
            code = "HOLD_UNCERTAIN"
        elif parents_codes and any(
            code != "COMPLETE_UNVERIFIED" for code in parents_codes
        ):
            code = "WAIT_DEPENDENCY"
        else:
            code = "READY_MOCK_ONLY"
        decisions.append(code)
    return tuple(decisions)


@pytest.mark.parametrize("shape", _SHAPES)
def test_all_small_dag_state_images_match_deny_only_reference(shape):
    valid = invalid = 0
    for states in product(_STATES, repeat=4):
        steps = tuple(
            ReadRecoveryStep(
                _NAMES[index], "math.sum",
                tuple(_NAMES[parent] for parent in parents), state,
                "a" * 64 if state == "SUCCEEDED" else None,
            )
            for index, (parents, state) in enumerate(zip(shape, states, strict=True))
        )
        expected = _reference(states, shape)
        if expected is None:
            invalid += 1
            with pytest.raises(DetachedReadRecoveryRejected):
                schedule_detached_read_recovery(_REQUEST, steps)
            continue
        valid += 1
        report = schedule_detached_read_recovery(_REQUEST, steps)
        assert tuple(item.disposition for item in report.decisions) == expected
        assert tuple(item.step_id for item in report.decisions) == _NAMES
        assert report == schedule_detached_read_recovery(_REQUEST, steps)
        assert report.dispatch_authorized is False
        assert report.automatic_replay_authorized is False
        assert report.external_outcome_verified is False
        assert len(report.schedule_digest) == 64
    assert valid > 0 and invalid > 0
    assert valid + invalid == 5**4


@pytest.mark.parametrize("dependencies", (
    (_NAMES[2],),                 # forward reference
    (_NAMES[1],),                 # self dependency
    (_NAMES[0], _NAMES[0]),      # duplicate dependency
    (_NAMES[1], _NAMES[0]),      # noncanonical order
))
def test_malformed_dependency_shapes_fail_without_execution(dependencies):
    steps = (
        ReadRecoveryStep(_NAMES[0], "math.sum", (), "SUCCEEDED", "b" * 64),
        ReadRecoveryStep(_NAMES[1], "math.sum", dependencies, "NOT_STARTED"),
    )
    with pytest.raises(DetachedReadRecoveryRejected):
        schedule_detached_read_recovery(_REQUEST, steps)
