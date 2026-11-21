"""Run906: detached synthetic V3 numerical admission remains exact and inert.

No GPU, external compute, candidate weights, training or approval checks run.
These local numerical examples are not a runtime identity/permission witness.
"""

from __future__ import annotations

import math
from dataclasses import replace

import pytest

from ark import v3_detached_preflight_crossbind as mod


def _fixtures():
    key = "a" * 64
    return (
        mod.DetachedV3Snapshot("offline-fixture:0", 8.0, key, 2),
        mod.DetachedV3Evidence(
            "offline-fixture:0", 8.0, key, 4096.0, 8192.0, 120.0,
        ),
    )


def test_exact_vram_and_wall_boundary_stays_non_authorizing():
    snapshot, evidence = _fixtures()
    report = mod.review_detached_v3_preflight(snapshot, evidence)
    assert report.checks == (
        "device", "capacity", "tokenizer_probe",
        "peak_vram_order", "wall_clock_budget",
    )
    assert report.independent_provenance_verified is False
    assert report.training_authorized is False
    assert report.paid_compute_authorized is False
    assert report.candidate_promotion_authorized is False


@pytest.mark.parametrize(("field", "value"), (
    ("peak_reserved_vram_mib", math.nextafter(8192.0, math.inf)),
    ("peak_vram_mib", math.nextafter(8192.0, math.inf)),
    ("wall_seconds", math.nextafter(120.0, math.inf)),
    ("peak_vram_mib", -0.0),
    ("peak_reserved_vram_mib", float("nan")),
))
def test_slightly_outside_numerical_boundaries_rejected(field, value):
    snapshot, evidence = _fixtures()
    with pytest.raises(mod.DetachedV3PreflightRejected):
        mod.review_detached_v3_preflight(
            snapshot, replace(evidence, **{field: value}),
        )


@pytest.mark.parametrize("field", (
    "peak_vram_mib", "peak_reserved_vram_mib", "wall_seconds",
))
def test_unrepresentable_large_integer_never_enters_digest(field):
    snapshot, evidence = _fixtures()
    with pytest.raises(mod.DetachedV3PreflightRejected):
        mod.review_detached_v3_preflight(
            snapshot, replace(evidence, **{field: 10**1000}),
        )


@pytest.mark.parametrize("field", ("capacity_gib", "reported_capacity_gib"))
def test_precision_losing_integer_capacity_is_not_equivalent(field):
    snapshot, evidence = _fixtures()
    if field == "capacity_gib":
        snapshot = replace(snapshot, capacity_gib=2**53 + 1)
    else:
        evidence = replace(evidence, reported_capacity_gib=2**53 + 1)
    with pytest.raises(mod.DetachedV3PreflightRejected):
        mod.review_detached_v3_preflight(snapshot, evidence)


def test_exact_device_pair_rebinding_changes_untrusted_evidence_digest():
    snapshot, evidence = _fixtures()
    old = mod.review_detached_v3_preflight(snapshot, evidence)
    new = mod.review_detached_v3_preflight(
        replace(snapshot, device="offline-fixture:1"),
        replace(evidence, device="offline-fixture:1"),
    )
    assert new.digest != old.digest
    assert new.training_authorized is False
