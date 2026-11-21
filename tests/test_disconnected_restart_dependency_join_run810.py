"""Restart joins never turn synthetic DAG or journal evidence into permission."""

from __future__ import annotations

from dataclasses import replace

import pytest

from ark.agency.contracts import Effect, StepState
from ark.agency.disconnected_dependency_quarantine_projection import (
    DisconnectedDependencyClaim,
    DisconnectedDependencyHold,
    DisconnectedDependencyProjection,
    review_disconnected_dependency_quarantine,
)
from ark.agency.disconnected_restart_dependency_join import (
    DisconnectedRestartDependencyRejected,
    review_disconnected_restart_dependency,
)
from ark.agency.planner_journal_review import SyntheticPlanRecovery, SyntheticPlanTail
from ark.agency.synthetic_write_quarantine_matrix_review import (
    SyntheticWriteStoreObservation,
)

_TOPOLOGY = "plan_" + "a" * 64
_TAIL = SyntheticPlanTail(
    _TOPOLOGY, 0, "pevt_" + "b" * 64, "pstate_" + "c" * 64, -1,
)
_CLAIMS = (
    DisconnectedDependencyClaim("a", Effect.WRITE, StepState.PENDING),
    DisconnectedDependencyClaim("b", Effect.READ, StepState.PENDING, ("a",)),
    DisconnectedDependencyClaim("c", Effect.READ, StepState.RUNNING),
)


def _fixture(
    claims: tuple[DisconnectedDependencyClaim, ...] = _CLAIMS,
) -> tuple[SyntheticPlanRecovery, DisconnectedDependencyProjection]:
    rows = tuple(
        SyntheticWriteStoreObservation(
            item.step_id, item.state.value, "absent", "absent", "absent",
        ) for item in claims if item.effect is Effect.WRITE
    )
    projection = review_disconnected_dependency_quarantine(
        topology_digest=_TOPOLOGY,
        claims=claims,
        independently_expected_write_ids=tuple(
            item.step_id for item in claims if item.effect is Effect.WRITE
        ),
        observations=rows,
    )
    recovered = SyntheticPlanRecovery(
        _TAIL,
        tuple((item.step_id, item.state.value, 0) for item in claims),
        tuple(item.step_id for item in claims if item.state is StepState.RUNNING),
    )
    return recovered, projection


def _join(
    *,
    recovered: SyntheticPlanRecovery | None = None,
    projection: DisconnectedDependencyProjection | None = None,
    claims: tuple[DisconnectedDependencyClaim, ...] = _CLAIMS,
    retained: SyntheticPlanTail = _TAIL,
):
    basic_recovery, basic_projection = _fixture()
    return review_disconnected_restart_dependency(
        recovered=basic_recovery if recovered is None else recovered,
        dependency=basic_projection if projection is None else projection,
        claims=claims,
        retained_tail=retained,
    )


def test_restart_join_keeps_all_steps_inert_and_running_unknown() -> None:
    result = _join()
    assert tuple((item.step_id, item.reason, item.outcome_unknown)
                 for item in result.holds) == (
        ("a", "QUARANTINE_WRITE_ALL_STATES", False),
        ("b", "HOLD_TRANSITIVE_WRITE_ANCESTOR", False),
        ("c", "HOLD_RUNNING_READ_UNCERTAIN", True),
    )
    assert result.uncertain_step_ids == ("c",)
    assert result.dispatch_authorized is False
    assert result.automatic_replay_authorized is False
    assert result.external_outcome_verified is False
    assert result.trusted_provenance_verified is False
    assert len(result.review_sha256) == 64
    assert _join() == result


@pytest.mark.parametrize(
    ("invalid", "expected"),
    (
        ("wrong-status", "state mismatch"),
        ("wrong-step", "status mismatch"),
        ("wrong-revision", "status mismatch"),
        ("bool-revision", "status mismatch"),
        ("negative-revision", "status mismatch"),
        ("oversized-revision", "status mismatch"),
        ("extra-status", "input type or budget"),
        ("missing-status", "input type or budget"),
        ("running-omitted", "RUNNING/UNKNOWN"),
        ("running-duplicated", "RUNNING/UNKNOWN"),
        ("running-as-pending", "state mismatch"),
        ("wrong-topology", "epoch mismatch"),
        ("wrong-event-hash", "epoch mismatch"),
        ("invalid-tail", "tail invalid"),
        ("missing-retained", "input type or budget"),
        ("projection-digest", "epoch mismatch"),
        ("projection-topology", "epoch mismatch"),
        ("wrong-hold-reason", "reason changed"),
        ("wrong-hold-id", "identity mismatch"),
        ("missing-hold", "input type or budget"),
        ("extra-hold", "input type or budget"),
        ("swapped-holds", "identity mismatch"),
        ("wrong-claim-parent", "reason changed"),
        ("unknown-parent", "missing dependency"),
        ("cycle", "cyclic dependency"),
        ("unsorted-claims", "unsorted"),
        ("duplicate-claims", "unsorted"),
        ("invalid-claim-effect", "invalid dependency"),
        ("bad-surrogate", "invalid dependency"),
    ),
)
def test_restart_join_fail_closed_on_cross_evidence_disagreement(
    invalid: str, expected: str,
) -> None:
    recovered, projection = _fixture()
    claims = _CLAIMS
    retained = _TAIL
    statuses = recovered.step_statuses
    if invalid == "wrong-status":
        statuses = (("a", "running", 0),) + statuses[1:]
        recovered = replace(recovered, step_statuses=statuses,
                            ambiguous_running_steps=("a", "c"))
    elif invalid == "wrong-step":
        recovered = replace(recovered, step_statuses=(("wrong", "pending", 0),) + statuses[1:])
    elif invalid == "wrong-revision":
        recovered = replace(recovered, step_statuses=(("a", "pending", "0"),) + statuses[1:])
    elif invalid == "bool-revision":
        recovered = replace(recovered, step_statuses=(("a", "pending", True),) + statuses[1:])
    elif invalid == "negative-revision":
        recovered = replace(recovered, step_statuses=(("a", "pending", -1),) + statuses[1:])
    elif invalid == "oversized-revision":
        recovered = replace(recovered, step_statuses=(("a", "pending", 1 << 63),) + statuses[1:])
    elif invalid == "extra-status":
        recovered = replace(recovered, step_statuses=statuses + (("extra", "pending", 0),))
    elif invalid == "missing-status":
        recovered = replace(recovered, step_statuses=statuses[:-1])
    elif invalid == "running-omitted":
        recovered = replace(recovered, ambiguous_running_steps=())
    elif invalid == "running-duplicated":
        recovered = replace(recovered, ambiguous_running_steps=("c", "c"))
    elif invalid == "running-as-pending":
        recovered = replace(recovered, step_statuses=statuses[:2] + (("c", "pending", 0),),
                            ambiguous_running_steps=())
    elif invalid == "wrong-topology":
        recovered = replace(recovered, tail=replace(_TAIL, topology_digest="plan_" + "d" * 64))
    elif invalid == "wrong-event-hash":
        recovered = replace(recovered, tail=replace(_TAIL, event_hash="pevt_" + "d" * 64))
    elif invalid == "invalid-tail":
        recovered = replace(recovered, tail=replace(_TAIL, last_at_ms=0))
    elif invalid == "missing-retained":
        retained = None
    elif invalid == "projection-digest":
        projection = replace(projection, digest="not-a-digest")
    elif invalid == "projection-topology":
        projection = replace(projection, topology_digest="plan_" + "d" * 64)
    elif invalid == "wrong-hold-reason":
        projection = replace(projection, holds=(
            replace(projection.holds[0], reason="HOLD_UNAUTHORIZED_MOCK_REVIEW"),
        ) + projection.holds[1:])
    elif invalid == "wrong-hold-id":
        projection = replace(projection, holds=(
            replace(projection.holds[0], step_id="wrong"),
        ) + projection.holds[1:])
    elif invalid == "missing-hold":
        projection = replace(projection, holds=projection.holds[:-1])
    elif invalid == "extra-hold":
        projection = replace(projection, holds=projection.holds + (
            DisconnectedDependencyHold("z", "HOLD_UNAUTHORIZED_MOCK_REVIEW"),
        ))
    elif invalid == "swapped-holds":
        projection = replace(projection, holds=tuple(reversed(projection.holds)))
    elif invalid == "wrong-claim-parent":
        claims = (claims[0], replace(claims[1], depends_on=()), claims[2])
    elif invalid == "unknown-parent":
        claims = (claims[0], replace(claims[1], depends_on=("missing",)), claims[2])
    elif invalid == "cycle":
        claims = (replace(claims[0], depends_on=("b",)), claims[1], claims[2])
    elif invalid == "unsorted-claims":
        claims = (claims[1], claims[0], claims[2])
    elif invalid == "duplicate-claims":
        claims = (claims[0], claims[0], claims[2])
    elif invalid == "invalid-claim-effect":
        claims = (replace(claims[0], effect="write"), claims[1], claims[2])
    elif invalid == "bad-surrogate":
        claims = (replace(claims[0], step_id="a\ud800"), claims[1], claims[2])
    with pytest.raises(DisconnectedRestartDependencyRejected, match=expected):
        review_disconnected_restart_dependency(
            recovered=recovered,
            dependency=projection,
            claims=claims,
            retained_tail=retained,
        )


@pytest.mark.parametrize(
    ("state", "reason"),
    (
        (StepState.SUCCEEDED, "HOLD_TERMINAL_READ_UNVERIFIED"),
        (StepState.FAILED, "HOLD_TERMINAL_READ_UNVERIFIED"),
        (StepState.BLOCKED, "HOLD_TERMINAL_READ_UNVERIFIED"),
        (StepState.CANCELLED, "HOLD_TERMINAL_READ_UNVERIFIED"),
        (StepState.PENDING, "HOLD_UNAUTHORIZED_MOCK_REVIEW"),
    ),
)
def test_non_write_read_also_never_receives_execution_permission(
    state: StepState, reason: str,
) -> None:
    claims = (_CLAIMS[0], _CLAIMS[1], replace(_CLAIMS[2], state=state))
    recovery, projection = _fixture(claims)
    result = review_disconnected_restart_dependency(
        recovered=recovery, dependency=projection,
        claims=claims, retained_tail=_TAIL,
    )
    assert result.holds[-1].reason == reason
    assert result.uncertain_step_ids == ()
    assert result.automatic_replay_authorized is False
