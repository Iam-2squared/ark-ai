"""Disconnected full-DAG WRITE ancestry is a hold, never a replay permit."""

from __future__ import annotations

from dataclasses import replace

import pytest

from ark.agency.contracts import Effect, StepState
from ark.agency.disconnected_dependency_quarantine_projection import (
    DisconnectedDependencyClaim,
    DisconnectedDependencyQuarantineRejected,
    review_disconnected_dependency_quarantine,
)
from ark.agency.synthetic_write_quarantine_matrix_review import (
    SyntheticWriteStoreObservation,
)

_TOPOLOGY = "plan_" + "a" * 64


def _claim(
    name: str,
    effect: Effect = Effect.READ,
    state: StepState = StepState.PENDING,
    parents: tuple[str, ...] = (),
) -> DisconnectedDependencyClaim:
    return DisconnectedDependencyClaim(name, effect, state, parents)


def _matrix(
    claims: tuple[DisconnectedDependencyClaim, ...],
    *,
    expected: tuple[str, ...] | None = None,
    rows: tuple[SyntheticWriteStoreObservation, ...] | None = None,
):
    writes = tuple(item.step_id for item in claims if item.effect is Effect.WRITE)
    if expected is None:
        expected = writes
    if rows is None:
        rows = tuple(
            SyntheticWriteStoreObservation(
                item.step_id, item.state.value, "absent", "absent", "absent"
            )
            for item in claims
            if item.effect is Effect.WRITE
        )
    return review_disconnected_dependency_quarantine(
        topology_digest=_TOPOLOGY,
        claims=claims,
        independently_expected_write_ids=expected,
        observations=rows,
    )


def test_transitive_write_quarantine_propagates_through_read_chain() -> None:
    claims = (
        _claim("a", Effect.WRITE),
        _claim("b", parents=("a",)),
        _claim("c", parents=("b",)),
        _claim("d"),
        _claim("e", parents=("d",)),
    )
    report = _matrix(claims)
    reasons = {item.step_id: item.reason for item in report.holds}
    assert reasons == {
        "a": "QUARANTINE_WRITE_ALL_STATES",
        "b": "HOLD_TRANSITIVE_WRITE_ANCESTOR",
        "c": "HOLD_TRANSITIVE_WRITE_ANCESTOR",
        "d": "HOLD_UNAUTHORIZED_MOCK_REVIEW",
        "e": "HOLD_DEPENDENCY_UNVERIFIED",
    }
    assert report.dispatch_authorized is False
    assert report.automatic_replay_authorized is False
    assert report.external_outcome_verified is False
    assert report.independent_custody_proven is False
    assert len(report.digest) == 64


@pytest.mark.parametrize(
    "state",
    (
        StepState.PENDING,
        StepState.RUNNING,
        StepState.SUCCEEDED,
        StepState.FAILED,
        StepState.BLOCKED,
    ),
)
def test_every_matrix_compatible_write_state_is_quarantined(state: StepState) -> None:
    report = _matrix((_claim("write", Effect.WRITE, state),))
    assert report.holds[0].reason == "QUARANTINE_WRITE_ALL_STATES"


@pytest.mark.parametrize(
    ("state", "reason"),
    (
        (StepState.PENDING, "HOLD_UNAUTHORIZED_MOCK_REVIEW"),
        (StepState.RUNNING, "HOLD_RUNNING_READ_UNCERTAIN"),
        (StepState.SUCCEEDED, "HOLD_TERMINAL_READ_UNVERIFIED"),
        (StepState.FAILED, "HOLD_TERMINAL_READ_UNVERIFIED"),
        (StepState.BLOCKED, "HOLD_TERMINAL_READ_UNVERIFIED"),
        (StepState.CANCELLED, "HOLD_TERMINAL_READ_UNVERIFIED"),
    ),
)
def test_independent_read_state_cannot_grant_tool_execution(
    state: StepState, reason: str,
) -> None:
    report = _matrix((_claim("a", Effect.WRITE), _claim("b", state=state)))
    assert report.holds[1].reason == reason


@pytest.mark.parametrize(
    "claims",
    (
        (_claim("a", Effect.WRITE, parents=("missing",)),),
        (_claim("a", Effect.WRITE, parents=("a",)),),
        (_claim("a", Effect.WRITE, parents=("b",)), _claim("b", parents=("a",))),
        (_claim("a", Effect.WRITE, parents=("b",)), _claim("b", parents=("c",)),
         _claim("c", parents=("a",))),
        (_claim("b", Effect.WRITE), _claim("a")),
        (_claim("a", Effect.WRITE), _claim("a")),
        (_claim("a", Effect.WRITE, parents=("b", "b")), _claim("b")),
    ),
)
def test_invalid_topology_is_rejected_before_any_classification(
    claims: tuple[DisconnectedDependencyClaim, ...],
) -> None:
    with pytest.raises(DisconnectedDependencyQuarantineRejected):
        _matrix(claims)


def test_missing_expected_write_identity_is_rejected() -> None:
    with pytest.raises(DisconnectedDependencyQuarantineRejected, match="WRITE inventory"):
        _matrix((_claim("a", Effect.WRITE),), expected=("wrong",))


def test_extra_observation_is_rejected() -> None:
    rows = (
        SyntheticWriteStoreObservation("a", "pending", "absent", "absent", "absent"),
        SyntheticWriteStoreObservation("b", "pending", "absent", "absent", "absent"),
    )
    with pytest.raises(DisconnectedDependencyQuarantineRejected):
        _matrix((_claim("a", Effect.WRITE),), rows=rows)


def test_write_cancelled_is_denied_not_coerced_to_pending() -> None:
    with pytest.raises(DisconnectedDependencyQuarantineRejected, match="matrix"):
        _matrix((_claim("a", Effect.WRITE, StepState.CANCELLED),))


def test_local_matrix_evidence_changes_result_without_releasing_write() -> None:
    claims = (_claim("a", Effect.WRITE), _claim("b", parents=("a",)))
    original = _matrix(claims)
    rows = (
        SyntheticWriteStoreObservation(
            "a", "pending", "present", "present", "present",
        ),
    )
    changed = _matrix(claims, rows=rows)
    assert original.matrix_digest != changed.matrix_digest
    assert original.digest != changed.digest
    assert changed.holds == original.holds
    assert changed.dispatch_authorized is False


def test_field_reflection_does_not_turn_an_old_result_into_authority() -> None:
    claims = (_claim("a", Effect.WRITE), _claim("b", parents=("a",)))
    first = _matrix(claims)
    second = _matrix(claims)
    assert first == second
    updated = (replace(claims[0], state=StepState.RUNNING), claims[1])
    assert _matrix(updated).digest != first.digest
