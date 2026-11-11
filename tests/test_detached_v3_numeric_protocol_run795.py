"""Exact-type, immutable-protocol checks for the detached free-only V3 reviewer."""

from __future__ import annotations

from dataclasses import replace

import pytest

from ark import v3_detached_preflight_crossbind as mod

_SHA = "a" * 64


def _valid():
    return (
        mod.DetachedV3Snapshot("cuda:0", 12.0, _SHA, 20),
        mod.DetachedV3Evidence("cuda:0", 12.0, _SHA, 4096.0, 6144.0, 300.0),
    )


@pytest.mark.parametrize(("side", "field", "invalid"), (
    ("snapshot", "capacity_gib", 2**53 + 1),
    ("evidence", "reported_capacity_gib", 2**53 + 1),
    ("evidence", "peak_vram_mib", 2**53 + 1),
    ("evidence", "wall_seconds", 2**53 + 1),
))
def test_precision_losing_integers_rejected_without_running_candidate(
    side, field, invalid,
):
    snapshot, evidence = _valid()
    if side == "snapshot":
        snapshot = replace(snapshot, **{field: invalid})
        evidence = replace(evidence, reported_capacity_gib=float(invalid))
    else:
        evidence = replace(evidence, **{field: invalid})
        if field == "reported_capacity_gib":
            snapshot = replace(snapshot, capacity_gib=float(invalid))
    with pytest.raises(mod.DetachedV3PreflightRejected):
        mod.review_detached_v3_preflight(snapshot, evidence)


@pytest.mark.parametrize("mutated", (True, 4097, -1))
def test_metadata_byte_limit_cannot_be_replaced(monkeypatch, mutated):
    snapshot, evidence = _valid()
    with monkeypatch.context() as patch:
        patch.setattr(mod, "_MAX_BYTES", mutated)
        with pytest.raises(mod.DetachedV3PreflightRejected, match="protocol"):
            mod.review_detached_v3_preflight(snapshot, evidence)


@pytest.mark.parametrize("carrier", (
    "DetachedV3Snapshot",
    "DetachedV3Evidence",
    "DetachedV3PreflightReview",
))
def test_substituted_attribute_lookup_denied_before_getter_runs(
    monkeypatch, carrier,
):
    snapshot, evidence = _valid()
    accessed = []

    def malicious(self, name):
        accessed.append(name)
        return object.__getattribute__(self, name)

    with monkeypatch.context() as patch:
        patch.setattr(getattr(mod, carrier), "__getattribute__", malicious)
        with pytest.raises(mod.DetachedV3PreflightRejected, match="protocol"):
            mod.review_detached_v3_preflight(snapshot, evidence)
    assert not accessed


def test_review_constructor_cannot_be_rebound(monkeypatch):
    snapshot, evidence = _valid()
    calls = []

    def malicious(self, *args, **kwargs):
        calls.append((args, kwargs))

    with monkeypatch.context() as patch:
        patch.setattr(mod.DetachedV3PreflightReview, "__init__", malicious)
        with pytest.raises(mod.DetachedV3PreflightRejected, match="protocol"):
            mod.review_detached_v3_preflight(snapshot, evidence)
    assert calls == []


def test_review_fields_cannot_be_rebound_before_digest_or_denial_check(monkeypatch):
    snapshot, evidence = _valid()
    with monkeypatch.context() as patch:
        patch.setattr(mod.DetachedV3PreflightReview, "checks", property(lambda _: ()))
        with pytest.raises(mod.DetachedV3PreflightRejected, match="protocol"):
            mod.review_detached_v3_preflight(snapshot, evidence)


def test_normal_synthetic_review_still_never_authorizes_spend():
    snapshot, evidence = _valid()
    report = mod.review_detached_v3_preflight(snapshot, evidence)
    assert report.training_authorized is False
    assert report.paid_compute_authorized is False
    assert report.candidate_promotion_authorized is False
    assert report.independent_provenance_verified is False
