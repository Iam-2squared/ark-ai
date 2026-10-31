"""Cross-plan reservation collision review for disconnected synthetic WRITE claims.

A uniqueness check on caller-supplied claims is NOT durable uniqueness,
identity/consent proof, external exactly-once execution, or retry authority.
No database, scheduler, clock, registry, or actual tool is accessed.
"""

from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass, field

_PLAN = re.compile(r"plan_[0-9a-f]{64}\Z")
_STEP = re.compile(r"step_[0-9a-f]{16}\Z")
_SLOT = re.compile(r"slot_[0-9a-f]{64}\Z")
_STATES = frozenset((
    "PENDING", "RUNNING", "UNKNOWN", "SUCCEEDED", "FAILED", "CANCELLED", "BLOCKED",
))
_MAX_PLANS = 16
_MAX_STEPS = 24
_MAX_REVISION = 2**63 - 1
_MAX_PAYLOAD = 65_536
_DOMAIN = b"ARK-detached-global-write-reservation-review-v1\0"


class ReservationOverlapRejected(ValueError):
    """Ambiguous or malformed synthetic cross-plan WRITE reservation set."""


@dataclass(frozen=True, slots=True)
class DetachedWriteReservationClaim:
    step_id: str = field(repr=False)
    reservation_id: str = field(repr=False)
    state: str


@dataclass(frozen=True, slots=True)
class DetachedPlanReservationClaims:
    plan_id: str = field(repr=False)
    revision: int
    writes: tuple[DetachedWriteReservationClaim, ...] = field(repr=False)


@dataclass(frozen=True, slots=True)
class DetachedReservationOverlapReview:
    plan_count: int
    write_count: int
    uncertain_write_count: int
    fingerprint: str

    @property
    def durable_uniqueness_proven(self) -> bool:
        return False

    @property
    def exact_once_effect_proven(self) -> bool:
        return False

    @property
    def automatic_retry_authorized(self) -> bool:
        return False

    @property
    def write_dispatch_authorized(self) -> bool:
        return False

    @property
    def issuer_or_consent_verified(self) -> bool:
        return False


def review_disconnected_reservation_overlap(
    plans: tuple[DetachedPlanReservationClaims, ...],
) -> DetachedReservationOverlapReview:
    """Reject aliased WRITE occurrences across the complete claimed plan set.

    No information outside this exact tuple is inspected. A successful review
    is only a bound diagnostic for these synthetic in-memory claims; it must
    never be interpreted as permission to execute, advance a cursor or replay.
    """
    if (
        type(plans) is not tuple or not 1 <= len(plans) <= _MAX_PLANS
        or any(type(plan) is not DetachedPlanReservationClaims for plan in plans)
    ):
        raise ReservationOverlapRejected("exact bounded cross-plan reservation set required")
    original_plans = plans
    plan_carriers = tuple(plans)
    originals = tuple((plan.plan_id, plan.revision, plan.writes) for plan in plans)
    step_carriers = tuple(tuple(plan.writes) if type(plan.writes) is tuple else ()
                          for plan in plans)
    step_fields = tuple(tuple((s.step_id, s.reservation_id, s.state)
                              for s in steps if type(s) is DetachedWriteReservationClaim)
                        for steps in step_carriers)

    def epoch() -> None:
        if plans is not original_plans or len(plans) != len(plan_carriers):
            raise ReservationOverlapRejected("plan sequence changed during review")
        for plan, original_plan, original_values, steps, saved in zip(
            plans, plan_carriers, originals, step_carriers, step_fields, strict=True,
        ):
            if (
                plan is not original_plan
                or any(a is not b for a, b in zip(
                    (plan.plan_id, plan.revision, plan.writes), original_values,
                    strict=True,
                ))
                or type(plan.writes) is not tuple or len(plan.writes) != len(steps)
                or len(saved) != len(steps)
            ):
                raise ReservationOverlapRejected("plan carrier changed during review")
            for current, old, frozen in zip(plan.writes, steps, saved, strict=True):
                if current is not old or any(a is not b for a, b in zip(
                    (current.step_id, current.reservation_id, current.state),
                    frozen, strict=True,
                )):
                    raise ReservationOverlapRejected("WRITE carrier changed during review")

    epoch()
    seen_plans: set[str] = set()
    seen_reservations: set[str] = set()
    write_count = 0
    uncertain = 0
    packed: list[tuple[object, ...]] = []
    for (plan_id, revision, writes), steps in zip(originals, step_fields, strict=True):
        epoch()
        if (
            type(plan_id) is not str or _PLAN.fullmatch(plan_id) is None
            or plan_id in seen_plans
            or type(revision) is not int or not 0 <= revision <= _MAX_REVISION
            or type(writes) is not tuple or not 1 <= len(writes) <= _MAX_STEPS
            or len(steps) != len(writes)
        ):
            raise ReservationOverlapRejected("duplicate or invalid plan snapshot")
        seen_plans.add(plan_id)
        seen_steps: set[str] = set()
        manifest: list[tuple[str, str, str]] = []
        for step_id, reservation_id, state in steps:
            if (
                type(step_id) is not str or _STEP.fullmatch(step_id) is None
                or step_id in seen_steps
                or type(reservation_id) is not str or _SLOT.fullmatch(reservation_id) is None
                or type(state) is not str or state not in _STATES
            ):
                raise ReservationOverlapRejected("invalid synthetic WRITE reservation")
            if reservation_id in seen_reservations:
                raise ReservationOverlapRejected("WRITE reservation reused across plan set")
            seen_steps.add(step_id)
            seen_reservations.add(reservation_id)
            write_count += 1
            if state in ("PENDING", "RUNNING", "UNKNOWN"):
                uncertain += 1
            manifest.append((step_id, reservation_id, state))
        packed.append((plan_id, revision, manifest))
        epoch()
    encoded = json.dumps(packed, ensure_ascii=True, separators=(",", ":")).encode("ascii")
    if len(encoded) > _MAX_PAYLOAD:
        raise ReservationOverlapRejected("cross-plan reservation byte budget exceeded")
    epoch()
    fingerprint = hashlib.sha256(_DOMAIN + encoded).hexdigest()
    epoch()
    review = DetachedReservationOverlapReview(len(plans), write_count, uncertain, fingerprint)
    epoch()
    if (
        type(review) is not DetachedReservationOverlapReview
        or type(review.plan_count) is not int or review.plan_count != len(plans)
        or type(review.write_count) is not int or review.write_count != write_count
        or type(review.uncertain_write_count) is not int
        or review.uncertain_write_count != uncertain
        or review.fingerprint is not fingerprint
    ):
        raise ReservationOverlapRejected("constructed reservation review changed")
    return review
