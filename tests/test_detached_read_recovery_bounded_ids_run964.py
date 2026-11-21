"""Run964: disconnected READ recovery bounds hostile labels before regex/graph work.

All data are synthetic in-memory request/step identifiers. READY_MOCK_ONLY
is not real authorization; no backend dispatch, clock, consent or replay.
"""

from __future__ import annotations

from dataclasses import replace

import pytest

from ark.agency.disconnected_read_recovery_schedule import (
    DetachedReadRecoveryRejected,
    ReadRecoveryStep,
    schedule_detached_read_recovery,
)

_REQUEST = "req_" + "a" * 32
_STEP_ONE = "step_" + "1" * 16
_STEP_TWO = "step_" + "2" * 16
_STEP_THREE = "step_" + "3" * 16


def _step(
    step_id: str = _STEP_ONE,
    *,
    depends_on: tuple[str, ...] = (),
    state: str = "NOT_STARTED",
    operation: str = "math.sum",
    result_sha256: str | None = None,
) -> ReadRecoveryStep:
    return ReadRecoveryStep(step_id, operation, depends_on, state, result_sha256)


@pytest.mark.parametrize(("field", "payload"), (
    ("step_id", "step_" + "a" * 100_000),
    ("step_id", "step_" + "\ud800" * 100),
    ("operation", "math.sum" + "X" * 100_000),
    ("operation", "math.sum" + "\ud800" * 100),
    ("state", "NOT_STARTED" + "X" * 100_000),
    ("result_sha256", "b" * 100_000),
))
def test_unbounded_or_noncanonical_step_field_never_becomes_recovery_authority(
    field: str, payload: str,
) -> None:
    original = _step(state="SUCCEEDED", result_sha256="b" * 64)
    altered = replace(original, **{field: payload})
    with pytest.raises(DetachedReadRecoveryRejected):
        schedule_detached_read_recovery(_REQUEST, (altered,))


@pytest.mark.parametrize("request_id", (
    "req_" + "a" * 100_000,
    "req_" + "\ud800" * 100,
))
def test_unbounded_request_identity_denied_without_starting_mock_work(
    request_id: str,
) -> None:
    with pytest.raises(DetachedReadRecoveryRejected):
        schedule_detached_read_recovery(request_id, (_step(),))


def test_unbounded_dependency_identity_rejected_before_sorting(
) -> None:
    graph = (
        _step(),
        _step(_STEP_TWO, depends_on=("step_" + "f" * 100_000,)),
    )
    with pytest.raises(DetachedReadRecoveryRejected):
        schedule_detached_read_recovery(_REQUEST, graph)


def test_valid_quarantine_and_independent_ready_branch_remain_deny_only() -> None:
    graph = (
        _step(state="RUNNING"),
        _step(_STEP_TWO, depends_on=(_STEP_ONE,)),
        _step(_STEP_THREE),
    )
    result = schedule_detached_read_recovery(_REQUEST, graph)
    assert tuple(d.disposition for d in result.decisions) == (
        "QUARANTINE_UNCERTAIN", "HOLD_UNCERTAIN", "READY_MOCK_ONLY",
    )
    assert result.dispatch_authorized is False
    assert result.automatic_replay_authorized is False
    assert result.external_outcome_verified is False
    assert len(result.schedule_digest) == 64
