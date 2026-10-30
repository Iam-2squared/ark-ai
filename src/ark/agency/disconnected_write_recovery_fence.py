"""Fail-closed, disconnected recovery triage for mixed READ/WRITE plans.

All states, hashes, and reservation IDs are untrusted caller claims. A
READY_MOCK_ONLY label is never execution permission. No backend, database,
clock or network is accessed, and ambiguous WRITE is never auto-replayed.
"""

from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass

_PLAN = re.compile(r"plan_[0-9a-f]{64}\Z")
_STEP = re.compile(r"step_[0-9a-f]{16}\Z")
_SHA = re.compile(r"[0-9a-f]{64}\Z")
_SLOT = re.compile(r"slot_[0-9a-f]{64}\Z")
_STATES = frozenset((
    "PENDING", "RUNNING", "SUCCEEDED", "FAILED", "CANCELLED", "BLOCKED", "UNKNOWN",
))
_DOMAIN = b"ARK-disconnected-mixed-recovery-fence-v1\0"
_MAX_STEPS = 24


class OfflineRecoveryFenceRejected(ValueError):
    """A synthetic mixed-plan recovery claim has unsafe topology or state."""


@dataclass(frozen=True, slots=True)
class OfflineRecoveryStepClaim:
    step_id: str
    effect: str
    depends_on: tuple[str, ...]
    state: str
    result_sha256: str | None = None
    reservation_id: str | None = None


@dataclass(frozen=True, slots=True)
class OfflineRecoveryDisposition:
    step_id: str
    code: str


@dataclass(frozen=True, slots=True)
class OfflineRecoveryFence:
    plan_id: str
    decisions: tuple[OfflineRecoveryDisposition, ...]
    digest: str

    @property
    def dispatch_authorized(self) -> bool:
        return False

    @property
    def automatic_replay_authorized(self) -> bool:
        return False

    @property
    def write_authorized(self) -> bool:
        return False

    @property
    def external_outcome_verified(self) -> bool:
        return False


# Pin original inert result carriers. Synthetic constructor injection must not
# replace an offline disposition with a fabricated dispatch-capable object.
_DISPOSITION_TYPE = OfflineRecoveryDisposition
_FENCE_TYPE = OfflineRecoveryFence


def review_disconnected_recovery_fence(
    plan_id: str, steps: tuple[OfflineRecoveryStepClaim, ...],
) -> OfflineRecoveryFence:
    """Classify every step without authorizing an effect or an uncertain retry.

    Topology must be an exact, ordered DAG. Terminal/uncertain ancestors
    propagate to PENDING descendants. No WRITE state is ever READY_MOCK_ONLY;
    reserved PENDING and UNKNOWN/RUNNING WRITE are quarantined.
    """
    if (
        type(plan_id) is not str or _PLAN.fullmatch(plan_id) is None
        or type(steps) is not tuple or not 1 <= len(steps) <= _MAX_STEPS
        or any(type(step) is not OfflineRecoveryStepClaim for step in steps)
    ):
        raise OfflineRecoveryFenceRejected("invalid exact mixed-plan claim")
    original_plan = plan_id
    original_steps = steps
    carriers = tuple(steps)
    saved = tuple(
        (s.step_id, s.effect, s.depends_on, s.state, s.result_sha256, s.reservation_id)
        for s in carriers
    )

    def epoch() -> None:
        if (
            plan_id is not original_plan or steps is not original_steps
            or len(steps) != len(carriers)
            or any(step is not old or any(
                now is not initial for now, initial in zip(
                    (step.step_id, step.effect, step.depends_on, step.state,
                     step.result_sha256, step.reservation_id), values, strict=True,
                )
            ) for step, old, values in zip(steps, carriers, saved, strict=True))
        ):
            raise OfflineRecoveryFenceRejected("mixed-plan carrier mutated during review")

    epoch()
    states: dict[str, str] = {}
    dispositions: dict[str, str] = {}
    decisions: list[OfflineRecoveryDisposition] = []
    decision_epoch: list[tuple[OfflineRecoveryDisposition, str, str]] = []
    canonical: list[tuple[object, ...]] = []

    def stable_decisions() -> None:
        if len(decisions) != len(decision_epoch) or any(
            type(current) is not _DISPOSITION_TYPE
            or current is not original
            or current.step_id is not name
            or current.code is not code
            for current, (original, name, code) in zip(
                decisions, decision_epoch, strict=True,
            )
        ):
            raise OfflineRecoveryFenceRejected("mixed-plan disposition changed")
    # No two WRITE steps may claim the same durable occurrence reservation.
    # A reused reservation ID creates ambiguous recovery ownership even when
    # both steps are otherwise held and no action is actually dispatched.
    reservations_seen: set[str] = set()
    for name, effect, deps, state, result, reservation in saved:
        epoch()
        stable_decisions()
        if (
            type(name) is not str or _STEP.fullmatch(name) is None or name in states
            or type(effect) is not str or effect not in ("READ", "WRITE")
            or type(deps) is not tuple or len(deps) > 16
            or any(type(dep) is not str or _STEP.fullmatch(dep) is None for dep in deps)
            or deps != tuple(sorted(set(deps)))
            or any(dep not in states for dep in deps)
            or type(state) is not str or state not in _STATES
            or (state == "SUCCEEDED") != (
                type(result) is str and _SHA.fullmatch(result) is not None
            )
            or (state != "SUCCEEDED" and result is not None)
            or (reservation is not None and (
                effect != "WRITE" or type(reservation) is not str
                or _SLOT.fullmatch(reservation) is None
            ))
        ):
            raise OfflineRecoveryFenceRejected("invalid ordered mixed-plan step")
        if reservation is not None:
            if reservation in reservations_seen:
                raise OfflineRecoveryFenceRejected("WRITE reservation reused across steps")
            reservations_seen.add(reservation)
        if state in ("SUCCEEDED", "RUNNING") and any(
            states[dep] != "SUCCEEDED" for dep in deps
        ):
            raise OfflineRecoveryFenceRejected("step became active before prerequisites")
        ancestors = tuple(dispositions[dep] for dep in deps)
        if state == "SUCCEEDED":
            code = "COMPLETE_UNVERIFIED"
        elif state in ("FAILED", "CANCELLED", "BLOCKED"):
            code = "TERMINAL"
        elif state in ("RUNNING", "UNKNOWN"):
            code = "QUARANTINE_WRITE_UNKNOWN" if effect == "WRITE" else "QUARANTINE_UNKNOWN"
        elif effect == "WRITE" and reservation is not None:
            code = "QUARANTINE_RESERVED_WRITE"
        elif any(x in ("TERMINAL", "HOLD_TERMINAL") for x in ancestors):
            code = "HOLD_TERMINAL"
        elif any(x in (
            "QUARANTINE_WRITE_UNKNOWN", "QUARANTINE_UNKNOWN",
            "QUARANTINE_RESERVED_WRITE", "HOLD_UNCERTAIN",
        ) for x in ancestors):
            code = "HOLD_UNCERTAIN"
        elif any(x != "COMPLETE_UNVERIFIED" for x in ancestors):
            code = "WAIT_DEPENDENCY"
        elif effect == "WRITE":
            code = "HELD_WRITE_APPROVAL"
        else:
            code = "READY_MOCK_ONLY"
        decision = OfflineRecoveryDisposition(name, code)
        if (
            type(decision) is not _DISPOSITION_TYPE
            or decision.step_id is not name
            or decision.code is not code
        ):
            raise OfflineRecoveryFenceRejected("invalid mixed-plan disposition carrier")
        decisions.append(decision)
        decision_epoch.append((decision, name, code))
        stable_decisions()
        states[name] = state
        dispositions[name] = code
        canonical.append((name, effect, deps, state, result, reservation, code))
        epoch()
        stable_decisions()
    encoded = json.dumps((plan_id, canonical), ensure_ascii=True,
                         separators=(",", ":")).encode("ascii")
    if len(encoded) > 24_576:
        raise OfflineRecoveryFenceRejected("mixed-plan metadata budget exceeded")
    epoch()
    stable_decisions()
    digest = hashlib.sha256(_DOMAIN + encoded).hexdigest()
    epoch()
    stable_decisions()
    frozen = tuple(decisions)
    review = OfflineRecoveryFence(plan_id, frozen, digest)
    epoch()
    stable_decisions()
    if (
        type(review) is not _FENCE_TYPE or review.plan_id is not plan_id
        or review.decisions is not frozen or review.digest is not digest
        # A synthetic recovery disposition is not a signed action grant.
        # Refuse an exact-type result whose descriptors were made to imply
        # WRITE, dispatch, automatic replay, or external outcome authority.
        or review.dispatch_authorized is not False
        or review.automatic_replay_authorized is not False
        or review.write_authorized is not False
        or review.external_outcome_verified is not False
    ):
        raise OfflineRecoveryFenceRejected("mixed-plan result carrier changed")
    return review
