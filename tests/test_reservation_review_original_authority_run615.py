"""Detached cross-plan reservation result must never acquire active authority.

No DB, external backend, billing, or WRITE dispatch is exercised.
"""
from __future__ import annotations

import pytest

import ark.agency.disconnected_reservation_overlap as mod

DENIALS = (
    "durable_uniqueness_proven", "exact_once_effect_proven",
    "automatic_retry_authorized", "write_dispatch_authorized",
    "issuer_or_consent_verified",
)


def _claim():
    return (mod.DetachedPlanReservationClaims(
        "plan_" + "a" * 64, 1,
        (mod.DetachedWriteReservationClaim(
            "step_" + "b" * 16, "slot_" + "c" * 64, "UNKNOWN",
        ),),
    ),)


@pytest.mark.parametrize("name", DENIALS)
@pytest.mark.parametrize("stage", ("preinstalled", "hash_callback"))
def test_false_returning_forged_authority_never_invoked(monkeypatch, name, stage):
    invoked = []

    def forged(_self):
        invoked.append(name)
        return False

    if stage == "preinstalled":
        monkeypatch.setattr(mod.DetachedReservationOverlapReview, name, property(forged))
    else:
        real_hash = mod.hashlib.sha256

        def during_hash(data):
            monkeypatch.setattr(
                mod.DetachedReservationOverlapReview, name, property(forged),
            )
            return real_hash(data)

        monkeypatch.setattr(mod.hashlib, "sha256", during_hash)

    with pytest.raises(
        mod.ReservationOverlapRejected, match="authority implementation changed",
    ):
        mod.review_disconnected_reservation_overlap(_claim())
    assert invoked == []


def test_counterfeit_class_with_copied_denials_cannot_construct(monkeypatch):
    constructed = []
    original = mod.DetachedReservationOverlapReview

    def fake_init(self, *args):
        constructed.append(args)

    namespace = {name: vars(original)[name] for name in DENIALS}
    namespace["__init__"] = fake_init
    counterfeit = type("CounterfeitReservationReview", (), namespace)
    monkeypatch.setattr(mod, "DetachedReservationOverlapReview", counterfeit)
    with pytest.raises(mod.ReservationOverlapRejected, match="authority"):
        mod.review_disconnected_reservation_overlap(_claim())
    assert constructed == []


def test_replaced_real_constructor_rejected_before_invocation(monkeypatch):
    constructed = []

    def fake_init(self, *args):
        constructed.append(args)

    monkeypatch.setattr(mod.DetachedReservationOverlapReview, "__init__", fake_init)
    with pytest.raises(mod.ReservationOverlapRejected, match="authority"):
        mod.review_disconnected_reservation_overlap(_claim())
    assert constructed == []


def test_result_class_swapped_after_hash_fails_before_construct(monkeypatch):
    constructed = []
    original = mod.DetachedReservationOverlapReview

    def fake_init(self, *args):
        constructed.append(args)

    counterfeit = type(
        "LateCounterfeitReservationReview", (),
        {**{key: vars(original)[key] for key in DENIALS}, "__init__": fake_init},
    )
    sha = mod.hashlib.sha256

    def during_hash(data):
        monkeypatch.setattr(mod, "DetachedReservationOverlapReview", counterfeit)
        return sha(data)

    monkeypatch.setattr(mod.hashlib, "sha256", during_hash)
    with pytest.raises(mod.ReservationOverlapRejected, match="authority"):
        mod.review_disconnected_reservation_overlap(_claim())
    assert constructed == []


def test_normal_result_remains_deterministic_and_deny_only():
    first = mod.review_disconnected_reservation_overlap(_claim())
    again = mod.review_disconnected_reservation_overlap(_claim())
    assert first == again
    assert (first.plan_count, first.write_count, first.uncertain_write_count) == (1, 1, 1)
    assert len(first.fingerprint) == 64
    assert all(getattr(first, name) is False for name in DENIALS)
