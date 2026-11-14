"""Detached V3 control-plane changes must fail before synthetic evidence reads."""

from __future__ import annotations

import pytest

from ark import v3_detached_preflight_crossbind as mod

_SHA = "a" * 64


def _valid():
    return (
        mod.DetachedV3Snapshot("cuda:0", 12.0, _SHA, 20),
        mod.DetachedV3Evidence("cuda:0", 12.0, _SHA, 4096.0, 6144.0, 300.0),
    )


@pytest.mark.parametrize(("name", "value"), (
    ("_FIELDS", {}),
    ("_HOOKS", ()),
    ("_ORIGINAL_SLOTS", {}),
    ("_DENIALS", ("training_authorized",)),
    ("_REVIEW_FIELDS", ("digest",)),
))
def test_replaced_protocol_control_objects_denied(monkeypatch, name, value):
    snapshot, evidence = _valid()
    with monkeypatch.context() as patch:
        patch.setattr(mod, name, value)
        with pytest.raises(mod.DetachedV3PreflightRejected, match="protocol"):
            mod.review_detached_v3_preflight(snapshot, evidence)


def test_in_place_snapshot_field_map_tamper_denied(monkeypatch):
    snapshot, evidence = _valid()
    with monkeypatch.context() as patch:
        patch.setitem(mod._FIELDS, mod.DetachedV3Snapshot, ("device",) * 4)
        with pytest.raises(mod.DetachedV3PreflightRejected, match="protocol"):
            mod.review_detached_v3_preflight(snapshot, evidence)


def test_in_place_original_descriptor_map_tamper_denied(monkeypatch):
    snapshot, evidence = _valid()
    with monkeypatch.context() as patch:
        patch.setitem(mod._ORIGINAL_SLOTS, mod.DetachedV3Snapshot, ())
        with pytest.raises(mod.DetachedV3PreflightRejected, match="protocol"):
            mod.review_detached_v3_preflight(snapshot, evidence)


def test_math_predicate_replacement_denied_before_execution(monkeypatch):
    snapshot, evidence = _valid()
    calls = []

    def malicious(_value):
        calls.append("called")
        return True

    with monkeypatch.context() as patch:
        patch.setattr(mod.math, "isfinite", malicious)
        with pytest.raises(mod.DetachedV3PreflightRejected, match="protocol"):
            mod.review_detached_v3_preflight(snapshot, evidence)
    assert not calls


def test_valid_detached_review_still_never_authorizes_cost_or_candidate():
    result = mod.review_detached_v3_preflight(*_valid())
    assert result.paid_compute_authorized is False
    assert result.training_authorized is False
    assert result.candidate_promotion_authorized is False
