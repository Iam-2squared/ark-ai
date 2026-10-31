"""Bounded cross-plan overlap proofs only; never grant mock or live WRITE."""

from dataclasses import FrozenInstanceError, replace

import pytest

from ark.agency import disconnected_reservation_overlap as module
from ark.agency.disconnected_reservation_overlap import (
    DetachedPlanReservationClaims,
    DetachedReservationOverlapReview,
    DetachedWriteReservationClaim,
    ReservationOverlapRejected,
    review_disconnected_reservation_overlap,
)


def slot(i):
    return "slot_" + f"{i:064x}"


def plan(i, *claims, revision=1):
    return DetachedPlanReservationClaims("plan_" + f"{i:064x}", revision, claims)


def claim(i, reservation=None, state="UNKNOWN"):
    return DetachedWriteReservationClaim(
        "step_" + f"{i:016x}", reservation or slot(i), state,
    )


def review(*plans):
    return review_disconnected_reservation_overlap(tuple(plans))


def test_unique_cross_plan_review_is_deny_only_and_deterministic():
    p1, p2 = plan(1, claim(1, state="UNKNOWN")), plan(2, claim(2, state="SUCCEEDED"))
    receipt = review(p1, p2)
    assert isinstance(receipt, DetachedReservationOverlapReview)
    assert receipt == review(p1, p2)
    assert (receipt.plan_count, receipt.write_count, receipt.uncertain_write_count) == (2, 2, 1)
    assert len(receipt.fingerprint) == 64
    for key in (
        "durable_uniqueness_proven", "exact_once_effect_proven", "automatic_retry_authorized",
        "write_dispatch_authorized", "issuer_or_consent_verified",
    ):
        assert getattr(receipt, key) is False
    assert "slot_" not in repr(receipt)
    assert "plan_" not in repr(p1)
    with pytest.raises(FrozenInstanceError):
        receipt.write_count = 99


def test_same_reservation_cross_plan_rejected_even_if_states_differ():
    with pytest.raises(ReservationOverlapRejected, match="reused"):
        review(plan(1, claim(1, state="SUCCEEDED")),
               plan(2, claim(2, reservation=slot(1), state="PENDING")))


def test_same_reservation_within_plan_rejected():
    with pytest.raises(ReservationOverlapRejected, match="reused"):
        review(plan(1, claim(1), claim(2, reservation=slot(1))))


def test_duplicate_plan_rejected_even_if_revision_changes():
    with pytest.raises(ReservationOverlapRejected, match="duplicate"):
        review(plan(1, claim(1), revision=1), plan(1, claim(2), revision=2))


def test_duplicate_step_id_in_plan_rejected():
    with pytest.raises(ReservationOverlapRejected, match="invalid"):
        review(plan(1, claim(1), claim(1, reservation=slot(2))))


def test_same_step_id_across_different_plans_with_distinct_occurrence_is_allowed():
    result = review(plan(1, claim(1)), plan(2, claim(1, reservation=slot(2))))
    assert result.write_count == 2
    assert not result.write_dispatch_authorized


@pytest.mark.parametrize("state", [
    "PENDING", "RUNNING", "UNKNOWN", "SUCCEEDED", "FAILED", "CANCELLED", "BLOCKED",
])
def test_all_known_write_states_are_untrusted_claims(state):
    result = review(plan(1, claim(1, state=state)))
    assert result.uncertain_write_count == int(state in ("PENDING", "RUNNING", "UNKNOWN"))
    assert not result.exact_once_effect_proven


@pytest.mark.parametrize("bad", [
    plan(1, claim(1), revision=True),
    plan(1, claim(1), revision=-1),
    plan(1, claim(1), revision=2**63),
    plan(1, claim(1), revision=1.0),
    replace(plan(1, claim(1)), plan_id="PLAN_" + "1" * 64),
    replace(plan(1, claim(1)), writes=[]),
    replace(plan(1, claim(1)), writes=()),
    plan(1, claim(1, reservation="slot_" + "Z" * 64)),
    plan(1, claim(1, state="READY")),
    plan(1, replace(claim(1), step_id="STEP_" + "1" * 16)),
    plan(1, replace(claim(1), reservation_id=None)),
])
def test_malformed_claims_fail_closed(bad):
    with pytest.raises(ReservationOverlapRejected):
        review(bad)


def test_bounded_plan_count_and_exact_input_types():
    with pytest.raises(ReservationOverlapRejected):
        review_disconnected_reservation_overlap([plan(1, claim(1))])
    with pytest.raises(ReservationOverlapRejected):
        review_disconnected_reservation_overlap(())
    with pytest.raises(ReservationOverlapRejected):
        review(*[plan(i + 1, claim(i + 1)) for i in range(17)])
    with pytest.raises(ReservationOverlapRejected):
        review_disconnected_reservation_overlap(({},))


def test_bounded_write_count():
    result = review(plan(1, *(claim(i + 1) for i in range(24))))
    assert result.write_count == 24
    with pytest.raises(ReservationOverlapRejected):
        review(plan(1, *(claim(i + 1) for i in range(25))))


def test_fingerprint_separates_policy_order_revision_and_states():
    a, b = plan(1, claim(1)), plan(2, claim(2, state="SUCCEEDED"))
    base = review(a, b).fingerprint
    assert base != review(b, a).fingerprint
    assert base != review(replace(a, revision=2), b).fingerprint
    assert base != review(replace(a, writes=(claim(1, state="PENDING"),)), b).fingerprint


def test_frozen_carrier_reflective_mutation_during_hash_rejected(monkeypatch):
    item = claim(1)
    original = module.hashlib.sha256

    def interfere(data):
        object.__setattr__(item, "state", "RUNNING")
        return original(data)

    monkeypatch.setattr(module.hashlib, "sha256", interfere)
    with pytest.raises(ReservationOverlapRejected, match="changed"):
        review(plan(1, item))


def test_frozen_plan_tuple_reflective_substitution_rejected(monkeypatch):
    batch = plan(1, claim(1))
    original = module.hashlib.sha256

    def interfere(data):
        object.__setattr__(batch, "writes", (claim(1),))
        return original(data)

    monkeypatch.setattr(module.hashlib, "sha256", interfere)
    with pytest.raises(ReservationOverlapRejected, match="changed"):
        review(batch)


def test_original_carrier_is_exact_and_private():
    class FakePlan(DetachedPlanReservationClaims):
        pass
    class FakeClaim(DetachedWriteReservationClaim):
        pass
    with pytest.raises(ReservationOverlapRejected):
        review(FakePlan("plan_" + "a" * 64, 1, (claim(1),)))
    with pytest.raises(ReservationOverlapRejected):
        review(plan(1, FakeClaim("step_" + "a" * 16, slot(1), "UNKNOWN")))
    c = claim(1)
    assert "slot_" not in repr(c) and "step_" not in repr(c)
