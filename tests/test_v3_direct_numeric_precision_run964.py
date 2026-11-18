"""Run964: detached synthetic V3 numeric precision and overflow boundaries.

These values describe in-memory fixture metadata only. No GPU/device query,
real runtime, paid compute, Candidate, training or protected evaluation occurs.
A matching digest never authenticates independent custody or grants authority.
"""

from __future__ import annotations

from dataclasses import replace

import pytest

from ark.v3_detached_preflight_crossbind import (
    DetachedV3Evidence,
    DetachedV3PreflightRejected,
    DetachedV3Snapshot,
    review_detached_v3_preflight,
)


def _pair() -> tuple[DetachedV3Snapshot, DetachedV3Evidence]:
    probe = "c" * 64
    return (
        DetachedV3Snapshot("fixture:0", 8.0, probe, 10),
        DetachedV3Evidence("fixture:0", 8.0, probe, 1024.0, 2048.0, 15.0),
    )


@pytest.mark.parametrize(("field", "value"), (
    ("capacity_gib", (1 << 53) + 1),
    ("capacity_gib", 10**400),
    ("capacity_gib", 1e308),
    ("wall_clock_timeout_minutes", True),
    ("wall_clock_timeout_minutes", 1_000_001),
))
def test_direct_snapshot_numeric_invalidity_refuses_inert_review(
    field: str, value: object,
) -> None:
    snapshot, evidence = _pair()
    snapshot = replace(snapshot, **{field: value})
    if field == "capacity_gib":
        evidence = replace(evidence, reported_capacity_gib=value)
    with pytest.raises(DetachedV3PreflightRejected):
        review_detached_v3_preflight(snapshot, evidence)


@pytest.mark.parametrize(("field", "value"), (
    ("reported_capacity_gib", (1 << 53) + 1),
    ("peak_vram_mib", (1 << 53) + 1),
    ("peak_reserved_vram_mib", (1 << 53) + 1),
    ("wall_seconds", (1 << 53) + 1),
    ("wall_seconds", 10**400),
    ("wall_seconds", -0.0),
    ("peak_vram_mib", True),
    ("peak_reserved_vram_mib", float("inf")),
))
def test_direct_evidence_numeric_invalidity_refuses_inert_review(
    field: str, value: object,
) -> None:
    snapshot, evidence = _pair()
    evidence = replace(evidence, **{field: value})
    with pytest.raises(DetachedV3PreflightRejected):
        review_detached_v3_preflight(snapshot, evidence)


def test_direct_exact_integer_normalization_keeps_no_authority() -> None:
    snapshot, evidence = _pair()
    first = review_detached_v3_preflight(snapshot, evidence)
    second = review_detached_v3_preflight(
        replace(snapshot, capacity_gib=8),
        replace(evidence, reported_capacity_gib=8, peak_vram_mib=1024,
                peak_reserved_vram_mib=2048, wall_seconds=15),
    )
    assert first.digest == second.digest
    assert first.checks == second.checks
    for review in (first, second):
        assert review.independent_provenance_verified is False
        assert review.paid_compute_authorized is False
        assert review.training_authorized is False
        assert review.candidate_promotion_authorized is False


def test_direct_exact_vram_and_timeout_boundary_remains_denial_only() -> None:
    snapshot, evidence = _pair()
    review = review_detached_v3_preflight(
        snapshot,
        replace(
            evidence,
            peak_vram_mib=8192.0,
            peak_reserved_vram_mib=8192.0,
            wall_seconds=600.0,
        ),
    )
    assert len(review.digest) == 64
    assert review.independent_provenance_verified is False
    assert review.paid_compute_authorized is False
    assert review.training_authorized is False
    assert review.candidate_promotion_authorized is False
