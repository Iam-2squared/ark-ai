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
_STEP_TYPE = OfflineRecoveryStepClaim
_DISPOSITION_TYPE = OfflineRecoveryDisposition
_FENCE_TYPE = OfflineRecoveryFence
_STEP_MEMBERS = (
    "step_id", "effect", "depends_on", "state",
    "result_sha256", "reservation_id",
    "__init__", "__new__", "__getattribute__", "__getattr__",
)
_DISPOSITION_MEMBERS = (
    "step_id", "code",
    "__init__", "__new__", "__getattribute__", "__getattr__",
)
_FENCE_MEMBERS = (
    "plan_id", "decisions", "digest",
    "__init__", "__new__", "__getattribute__", "__getattr__",
)
_ORIGINAL_STEP_MEMBERS = tuple(
    vars(_STEP_TYPE).get(name) for name in _STEP_MEMBERS
)
_ORIGINAL_DISPOSITION_MEMBERS = tuple(
    vars(_DISPOSITION_TYPE).get(name) for name in _DISPOSITION_MEMBERS
)
_ORIGINAL_FENCE_MEMBERS = tuple(
    vars(_FENCE_TYPE).get(name) for name in _FENCE_MEMBERS
)
_ORIGINAL_DISPOSITION_INIT = vars(_DISPOSITION_TYPE)["__init__"]
_ORIGINAL_FENCE_INIT = vars(_FENCE_TYPE)["__init__"]
_FENCE_DENIAL_NAMES = (
    "dispatch_authorized", "automatic_replay_authorized",
    "write_authorized", "external_outcome_verified",
)
_ORIGINAL_FENCE_DENIALS = tuple(
    vars(_FENCE_TYPE)[name] for name in _FENCE_DENIAL_NAMES
)
# A synthetic recovery digest is not external-execution evidence, but a
# substituted hash/serializer/domain must never bless an unreviewed claim.
# Snapshot their original definitions before any reentrant result callback.
_ORIGINAL_HASHLIB = hashlib
_ORIGINAL_JSON = json
_ORIGINAL_SHA256 = hashlib.sha256
_ORIGINAL_DUMPS = json.dumps
_ORIGINAL_DOMAIN = _DOMAIN
# Freeze the admissible grammar and graph bound as well as the hash protocol.
# A substituted matcher is executable code: reject it BEFORE fullmatch() or
# any caller-supplied private step field can reach that replacement.
_ORIGINAL_PLAN = _PLAN
_ORIGINAL_STEP = _STEP
_ORIGINAL_SHA = _SHA
_ORIGINAL_SLOT = _SLOT
_ORIGINAL_STATES = _STATES
_ORIGINAL_MAX_STEPS = _MAX_STEPS


def _require_original_fence_denials() -> None:
    # Do not run a substituted getter even if it returns False. Report type
    # identity matters: copied original descriptors do not authenticate an
    # arbitrary new report constructor.
    if (
        OfflineRecoveryStepClaim is not _STEP_TYPE
        or OfflineRecoveryFence is not _FENCE_TYPE
        or OfflineRecoveryDisposition is not _DISPOSITION_TYPE
        or any(
            vars(_STEP_TYPE).get(name) is not original
            for name, original in zip(
                _STEP_MEMBERS, _ORIGINAL_STEP_MEMBERS, strict=True,
            )
        )
        or any(
            vars(_DISPOSITION_TYPE).get(name) is not original
            for name, original in zip(
                _DISPOSITION_MEMBERS, _ORIGINAL_DISPOSITION_MEMBERS, strict=True,
            )
        )
        or any(
            vars(_FENCE_TYPE).get(name) is not original
            for name, original in zip(
                _FENCE_MEMBERS, _ORIGINAL_FENCE_MEMBERS, strict=True,
            )
        )
        or vars(_DISPOSITION_TYPE).get("__init__") is not _ORIGINAL_DISPOSITION_INIT
        or vars(_FENCE_TYPE).get("__init__") is not _ORIGINAL_FENCE_INIT
        or any(
        vars(_FENCE_TYPE).get(name) is not original
        for name, original in zip(
            _FENCE_DENIAL_NAMES, _ORIGINAL_FENCE_DENIALS, strict=True,
        )
        )
    ):
        raise OfflineRecoveryFenceRejected(
            "mixed-plan authority descriptor changed"
        )
    if (
        _PLAN is not _ORIGINAL_PLAN
        or _STEP is not _ORIGINAL_STEP
        or _SHA is not _ORIGINAL_SHA
        or _SLOT is not _ORIGINAL_SLOT
        or _STATES is not _ORIGINAL_STATES
        or type(_MAX_STEPS) is not int
        or _MAX_STEPS != _ORIGINAL_MAX_STEPS
    ):
        raise OfflineRecoveryFenceRejected("mixed-plan grammar or budget changed")
    if (
        hashlib is not _ORIGINAL_HASHLIB
        or json is not _ORIGINAL_JSON
        or hashlib.sha256 is not _ORIGINAL_SHA256
        or json.dumps is not _ORIGINAL_DUMPS
        or _DOMAIN is not _ORIGINAL_DOMAIN
    ):
        raise OfflineRecoveryFenceRejected(
            "mixed-plan digest implementation or domain changed"
        )


def review_disconnected_recovery_fence(
    plan_id: str, steps: tuple[OfflineRecoveryStepClaim, ...],
) -> OfflineRecoveryFence:
    """Classify every step without authorizing an effect or an uncertain retry.

    Topology must be an exact, ordered DAG. Terminal/uncertain ancestors
    propagate to PENDING descendants. No WRITE state is ever READY_MOCK_ONLY;
    reserved PENDING and UNKNOWN/RUNNING WRITE are quarantined.
    """
    # Refuse oversized untrusted strings before the regex engine or JSON codec.
    # The canonical identity formats are fixed-width ASCII; no normalized or
    # truncated claimant can become a recovery, replay or dispatch receipt.
    # Must run before invoking regex.fullmatch on a replaceable module global.
    _require_original_fence_denials()
    if (
        type(plan_id) is not str or len(plan_id) != 69
        or _PLAN.fullmatch(plan_id) is None
        or type(steps) is not tuple or not 1 <= len(steps) <= _MAX_STEPS
        or any(type(step) is not OfflineRecoveryStepClaim for step in steps)
    ):
        raise OfflineRecoveryFenceRejected("invalid exact mixed-plan claim")
    _require_original_fence_denials()
    original_plan = plan_id
    original_steps = steps
    carriers = tuple(steps)
    saved = tuple(
        (s.step_id, s.effect, s.depends_on, s.state, s.result_sha256, s.reservation_id)
        for s in carriers
    )

    def epoch() -> None:
        _require_original_fence_denials()
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
        _require_original_fence_denials()
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
            type(name) is not str or len(name) != 21
            or _STEP.fullmatch(name) is None or name in states
            or type(effect) is not str or len(effect) > 5
            or effect not in ("READ", "WRITE")
            or type(deps) is not tuple or len(deps) > 16
            or any(type(dep) is not str or len(dep) != 21
                   or _STEP.fullmatch(dep) is None for dep in deps)
            or deps != tuple(sorted(set(deps)))
            or any(dep not in states for dep in deps)
            or type(state) is not str or len(state) > 9 or state not in _STATES
            or (state == "SUCCEEDED") != (
                type(result) is str and len(result) == 64
                and _SHA.fullmatch(result) is not None
            )
            or (state != "SUCCEEDED" and result is not None)
            or (reservation is not None and (
                effect != "WRITE" or type(reservation) is not str
                or len(reservation) != 69 or _SLOT.fullmatch(reservation) is None
            ))
        ):
            raise OfflineRecoveryFenceRejected("invalid ordered mixed-plan step")
        if reservation is not None:
            if reservation in reservations_seen:
                raise OfflineRecoveryFenceRejected("WRITE reservation reused across steps")
            reservations_seen.add(reservation)
        # FAILED is a terminal *started* claim, not an alternative to
        # BLOCKED: a failed child cannot have run before its prerequisites
        # succeeded. Keep CANCELLED/BLOCKED admissible as non-execution
        # terminal diagnostics when ancestors are unresolved.
        if state in ("SUCCEEDED", "FAILED", "RUNNING") and any(
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
        _require_original_fence_denials()
        decision = _DISPOSITION_TYPE(name, code)
        _require_original_fence_denials()
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
    _require_original_fence_denials()
    review = _FENCE_TYPE(plan_id, frozen, digest)
    epoch()
    stable_decisions()
    if (
        type(review) is not _FENCE_TYPE or review.plan_id is not plan_id
        or review.decisions is not frozen or review.digest is not digest
    ):
        raise OfflineRecoveryFenceRejected("mixed-plan result carrier changed")
    # A deny-only getter is executable Python. Refuse a replaced descriptor
    # before invoking it and verify every claim and decision after each call.
    for name in _FENCE_DENIAL_NAMES:
        _require_original_fence_denials()
        if getattr(review, name) is not False:
            raise OfflineRecoveryFenceRejected("mixed-plan result carrier changed")
        epoch()
        stable_decisions()
        if (
            type(review) is not _FENCE_TYPE
            or review.plan_id is not plan_id
            or review.decisions is not frozen
            or review.digest is not digest
        ):
            raise OfflineRecoveryFenceRejected("mixed-plan result carrier changed")
        _require_original_fence_denials()
    return review
