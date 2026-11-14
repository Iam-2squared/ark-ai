"""Synthetic V3 evidence consistency is not execution/promotion authorization."""

from __future__ import annotations

from dataclasses import replace

import pytest

from ark import v3_detached_preflight_crossbind as mod

_SHA = "a" * 64
_OTHER = "b" * 64


def _valid():
    snapshot = mod.DetachedV3Snapshot("cuda:0", 12.0, _SHA, 20)
    evidence = mod.DetachedV3Evidence(
        "cuda:0", 12.0, _SHA, 4096.0, 6144.0, 300.0,
    )
    return snapshot, evidence


def test_exact_synthetic_cross_binding_is_stable_and_never_authoritative():
    snapshot, evidence = _valid()
    a = mod.review_detached_v3_preflight(snapshot, evidence)
    b = mod.review_detached_v3_preflight(snapshot, evidence)
    assert a == b
    assert len(a.digest) == 64
    assert a.checks == (
        "device", "capacity", "tokenizer_probe", "peak_vram_order",
        "wall_clock_budget",
    )
    assert a.independent_provenance_verified is False
    assert a.training_authorized is False
    assert a.paid_compute_authorized is False
    assert a.candidate_promotion_authorized is False


@pytest.mark.parametrize(("side", "field", "value"), (
    ("evidence", "device", "cuda:1"),
    ("snapshot", "device", " cuda:0"),
    ("snapshot", "device", "cuda:0\n"),
    ("evidence", "tokenizer_probe_sha256", _OTHER),
    ("snapshot", "tokenizer_probe_sha256", "A" * 64),
    ("evidence", "reported_capacity_gib", 10.0),
    ("evidence", "peak_vram_mib", 7000.0),
    ("evidence", "peak_reserved_vram_mib", 13000.0),
    ("evidence", "wall_seconds", 1201.0),
    ("snapshot", "wall_clock_timeout_minutes", True),
    ("snapshot", "wall_clock_timeout_minutes", 0),
    ("snapshot", "capacity_gib", float("nan")),
    ("snapshot", "capacity_gib", float("inf")),
    ("evidence", "reported_capacity_gib", True),
    ("evidence", "peak_vram_mib", True),
    ("evidence", "peak_vram_mib", 0),
    ("evidence", "peak_vram_mib", -1),
    ("evidence", "peak_reserved_vram_mib", float("nan")),
    ("evidence", "peak_reserved_vram_mib", float("-inf")),
    ("evidence", "wall_seconds", float("inf")),
    ("evidence", "wall_seconds", False),
))
def test_frozen_runtime_evidence_cross_binding_denied(side, field, value):
    snapshot, evidence = _valid()
    if side == "snapshot":
        snapshot = replace(snapshot, **{field: value})
    else:
        evidence = replace(evidence, **{field: value})
    with pytest.raises(mod.DetachedV3PreflightRejected):
        mod.review_detached_v3_preflight(snapshot, evidence)


def test_snapshot_and_evidence_cannot_be_subclassed_into_review():
    snapshot, evidence = _valid()

    class Child(mod.DetachedV3Snapshot):
        pass

    child = Child("cuda:0", 12.0, _SHA, 20)
    # Subclass identity is not sufficient even with matching field values.
    with pytest.raises(mod.DetachedV3PreflightRejected):
        mod.review_detached_v3_preflight(child, evidence)
    with pytest.raises(mod.DetachedV3PreflightRejected):
        mod.review_detached_v3_preflight(snapshot, "not-evidence")


@pytest.mark.parametrize("field", (
    "training_authorized", "paid_compute_authorized",
    "candidate_promotion_authorized",
))
def test_rebound_denial_property_rejected_before_use(monkeypatch, field):
    snapshot, evidence = _valid()
    visited = []

    def malicious(_self):
        visited.append(field)
        return False

    with monkeypatch.context() as patch:
        patch.setattr(mod.DetachedV3PreflightReview, field, property(malicious))
        with pytest.raises(mod.DetachedV3PreflightRejected, match="protocol"):
            mod.review_detached_v3_preflight(snapshot, evidence)
    assert visited == []
