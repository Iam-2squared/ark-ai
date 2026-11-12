"""Disconnected dependency review refuses tampered carriers before matrix access."""

from __future__ import annotations

import re

import pytest

import ark.agency.disconnected_dependency_quarantine_projection as projection
from ark.agency.contracts import Effect, StepState
from ark.agency.synthetic_write_quarantine_matrix_review import (
    SyntheticWriteStoreObservation,
)

_TOPOLOGY = "plan_" + "a" * 64


def _review() -> projection.DisconnectedDependencyProjection:
    return projection.review_disconnected_dependency_quarantine(
        topology_digest=_TOPOLOGY,
        claims=(
            projection.DisconnectedDependencyClaim(
                "read", Effect.READ, StepState.PENDING, ("write",),
            ),
            projection.DisconnectedDependencyClaim(
                "write", Effect.WRITE, StepState.PENDING,
            ),
        ),
        independently_expected_write_ids=("write",),
        observations=(
            SyntheticWriteStoreObservation(
                "write", "pending", "absent", "absent", "absent",
            ),
        ),
    )


@pytest.mark.parametrize(
    ("name", "replacement"),
    (
        ("_PLAN", re.compile(r"plan_.*")),
        ("_DOMAIN", b"unbound-quarantine"),
        ("_MAX_STEPS", 129),
        ("_MAX_EDGES", 4097),
        ("_MAX_STEPS", True),
        ("Effect", object),
        ("StepState", object),
        ("DisconnectedDependencyClaim", object),
        ("DisconnectedDependencyHold", object),
        ("DisconnectedDependencyProjection", object),
        ("diagnose_disconnected_write_quarantine", lambda **_: None),
        ("heappush", lambda *_: None),
    ),
)
def test_rebound_protocol_denied_without_classifying(
    monkeypatch: pytest.MonkeyPatch, name: str, replacement: object,
) -> None:
    with monkeypatch.context() as patch:
        patch.setattr(projection, name, replacement)
        with pytest.raises(
            projection.DisconnectedDependencyQuarantineRejected, match="authority",
        ):
            _review()
    assert _review().automatic_replay_authorized is False


@pytest.mark.parametrize(
    ("cls", "field"),
    (
        (projection.DisconnectedDependencyClaim, "effect"),
        (projection.DisconnectedDependencyClaim, "step_id"),
        (projection.DisconnectedDependencyHold, "reason"),
        (projection.DisconnectedDependencyProjection, "holds"),
    ),
)
def test_rebound_carrier_field_rejected_before_getter(
    monkeypatch: pytest.MonkeyPatch, cls: type, field: str,
) -> None:
    def leak(_: object) -> object:
        raise AssertionError("untrusted carrier field was read")

    with monkeypatch.context() as patch:
        patch.setattr(cls, field, property(leak))
        with pytest.raises(
            projection.DisconnectedDependencyQuarantineRejected, match="authority",
        ):
            _review()


@pytest.mark.parametrize(
    "cls",
    (
        projection.DisconnectedDependencyClaim,
        projection.DisconnectedDependencyHold,
        projection.DisconnectedDependencyProjection,
    ),
)
def test_rebound_carrier_getattribute_rejected(
    monkeypatch: pytest.MonkeyPatch, cls: type,
) -> None:
    with monkeypatch.context() as patch:
        patch.setattr(cls, "__getattribute__", lambda *_: None)
        with pytest.raises(
            projection.DisconnectedDependencyQuarantineRejected, match="authority",
        ):
            _review()


def test_original_protocol_returns_only_denial_for_all_descendants() -> None:
    out = _review()
    assert tuple((hold.step_id, hold.reason) for hold in out.holds) == (
        ("read", "HOLD_TRANSITIVE_WRITE_ANCESTOR"),
        ("write", "QUARANTINE_WRITE_ALL_STATES"),
    )
    assert out.dispatch_authorized is False
    assert out.automatic_replay_authorized is False
    assert out.external_outcome_verified is False
    assert out.independent_custody_proven is False
