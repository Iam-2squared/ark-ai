"""Detached Planner evidence must match the actual canonical local DAG transcript."""

from __future__ import annotations

from dataclasses import replace

import pytest

import ark.agency.disconnected_dependency_digest_review as digest_review
from ark.agency.contracts import Effect, StepState
from ark.agency.disconnected_dependency_quarantine_projection import (
    DisconnectedDependencyClaim,
    DisconnectedDependencyHold,
    review_disconnected_dependency_quarantine,
)
from ark.agency.synthetic_write_quarantine_matrix_review import (
    SyntheticWriteStoreObservation,
)

_TOPOLOGY = "plan_" + "a" * 64
_CLAIMS = (
    DisconnectedDependencyClaim("a", Effect.WRITE, StepState.PENDING),
    DisconnectedDependencyClaim("b", Effect.READ, StepState.PENDING, ("a",)),
)


def _projection():
    return review_disconnected_dependency_quarantine(
        topology_digest=_TOPOLOGY,
        claims=_CLAIMS,
        independently_expected_write_ids=("a",),
        observations=(
            SyntheticWriteStoreObservation("a", "pending", "absent", "absent", "absent"),
        ),
    )


def test_canonical_synthetic_dag_projection_is_hash_self_consistent_only() -> None:
    projection = _projection()
    report = digest_review.review_detached_dependency_digest(
        claims=_CLAIMS, projection=projection,
    )
    assert report.topology_digest == _TOPOLOGY
    assert report.quarantine_digest == projection.digest
    assert len(report.review_sha256) == 64
    assert digest_review.review_detached_dependency_digest(
        claims=_CLAIMS, projection=projection,
    ) == report
    assert report.dispatch_authorized is False
    assert report.automatic_replay_authorized is False
    assert report.external_provenance_verified is False


@pytest.mark.parametrize(
    "case",
    (
        "forged-digest", "forged-matrix", "forged-hold-reason",
        "changed-claim-effect", "changed-claim-dependency", "swapped-claims",
        "bad-matrix-grammar", "extra-hold", "duplicate-claims",
        "missing-claim", "wrong-topology", "bool-state",
    ),
)
def test_detached_digest_refuses_forged_local_evidence(case: str) -> None:
    projection = _projection()
    claims = _CLAIMS
    if case == "forged-digest":
        projection = replace(projection, digest="f" * 64)
    elif case == "forged-matrix":
        projection = replace(projection, matrix_digest="quarantine_" + "f" * 64)
    elif case == "forged-hold-reason":
        projection = replace(projection, holds=(
            DisconnectedDependencyHold("a", "HOLD_TERMINAL_READ_UNVERIFIED"),
            projection.holds[1],
        ))
    elif case == "changed-claim-effect":
        claims = (replace(claims[0], effect=Effect.READ), claims[1])
    elif case == "changed-claim-dependency":
        claims = (claims[0], replace(claims[1], depends_on=()))
    elif case == "swapped-claims":
        claims = tuple(reversed(claims))
    elif case == "bad-matrix-grammar":
        projection = replace(projection, matrix_digest="0" * 64)
    elif case == "extra-hold":
        projection = replace(projection, holds=projection.holds + (
            DisconnectedDependencyHold("c", "HOLD_UNAUTHORIZED_MOCK_REVIEW"),
        ))
    elif case == "duplicate-claims":
        claims = (claims[0], claims[0])
    elif case == "missing-claim":
        claims = claims[:1]
    elif case == "wrong-topology":
        projection = replace(projection, topology_digest="plan_" + "f" * 64)
    elif case == "bool-state":
        claims = (replace(claims[0], state=True), claims[1])
    with pytest.raises(digest_review.DetachedDependencyDigestRejected):
        digest_review.review_detached_dependency_digest(
            claims=claims, projection=projection,
        )


@pytest.mark.parametrize("tamper", ("domain", "claim-slot", "result-authority"))
def test_protocol_tampering_rejected_before_any_stale_receipt_is_accepted(
    monkeypatch: pytest.MonkeyPatch, tamper: str,
) -> None:
    projection = _projection()
    original_result = digest_review.DetachedDependencyDigestReview
    with monkeypatch.context() as patch:
        if tamper == "domain":
            patch.setattr(digest_review.projection_module, "_DOMAIN", b"tampered")
        elif tamper == "claim-slot":
            patch.setattr(
                DisconnectedDependencyClaim, "step_id",
                property(lambda _: (_ for _ in ()).throw(
                    AssertionError("cannot invoke forged step ID getter")
                )),
            )
        else:
            patch.setattr(
                original_result, "dispatch_authorized",
                property(lambda _: True),
            )
        with pytest.raises(digest_review.DetachedDependencyDigestRejected):
            digest_review.review_detached_dependency_digest(
                claims=_CLAIMS, projection=projection,
            )
