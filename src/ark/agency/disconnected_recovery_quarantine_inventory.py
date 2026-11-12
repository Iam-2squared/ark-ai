"""Disconnected cross-domain restart quarantine inventory, not readiness authority.

Memory, Planner and local preaction logs were reviewed in *separate* epochs.
This aggregates bounded, synthetic, digest-only reports for operator diagnosis;
it cannot authenticate a clock, consent, a writer or any external side effect.
No SQLite connection, tool call, state mutation, replay or automatic recovery.
"""

from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass

from ..memory import ambiguous_commit_pair_review as memory_module
from . import disconnected_atomic_unknown_outcome_review as atomic_module
from . import disconnected_planner_slot_restart_bridge as planner_module

AtomicUnknownOutcomeReview = atomic_module.AtomicUnknownOutcomeReview
DisconnectedPlannerSlotBridge = planner_module.DisconnectedPlannerSlotBridge
MemoryAmbiguityPair = memory_module.MemoryAmbiguityPair

_DOMAIN = b"ARK-disconnected-recovery-quarantine-inventory-v1\0"
_SHA = re.compile(r"[0-9a-f]{64}\Z")
_OCC = re.compile(r"occ_[0-9a-f]{64}\Z")
_MAX_OCCURRENCES = 16
_MAX_STEPS = 24

_MEMORY_DISPOSITIONS = (
    "LOCAL_UNCHANGED_REVIEW",
    "MATCHING_ROW_MANUAL_REVIEW",
    "DIVERGED_MANUAL_REVIEW",
)
_ATOMIC_STATES = (
    "UNCHANGED", "LOCALLY_RECORDED", "PREEXISTING", "ADVANCED_OTHER",
)


class DisconnectedRecoveryInventoryRejected(ValueError):
    """Local observations cannot be combined even for manual triage."""


@dataclass(frozen=True, slots=True)
class DisconnectedRecoveryQuarantineInventory:
    plan_id: str
    memory_disposition: str
    held_step_count: int
    unknown_step_count: int
    observed_occurrence_count: int
    locally_present_count: int
    disposition: str
    inventory_sha256: str

    @property
    def manual_review_required(self) -> bool:
        return True

    @property
    def dispatch_authorized(self) -> bool:
        return False

    @property
    def automatic_replay_authorized(self) -> bool:
        return False

    @property
    def consent_authenticated(self) -> bool:
        return False

    @property
    def cross_store_atomicity_proven(self) -> bool:
        return False

    @property
    def external_effect_verified(self) -> bool:
        return False

    @property
    def trusted_clock_verified(self) -> bool:
        return False


_REPORT = DisconnectedRecoveryQuarantineInventory
_MEMORY = MemoryAmbiguityPair
_PLANNER = DisconnectedPlannerSlotBridge
_ATOMIC = AtomicUnknownOutcomeReview
_MEMORY_FIELDS = (
    "disposition", "retained_prefix_sha256", "observed_prefix_sha256",
    "observed_row_sha256", "triage_receipt_sha256",
    "outcome_receipt_sha256", "reconciliation_sha256",
)
_PLANNER_FIELDS = (
    "plan_id", "bundle_sha256", "slot_fingerprint", "held_step_ids",
    "unknown_step_ids", "reserved_write_count", "bridge_sha256",
)
_ATOMIC_FIELDS = (
    "occurrence_id", "local_state", "before_count", "observed_count",
    "locally_present",
)
_REPORT_FIELDS = tuple(_REPORT.__dataclass_fields__)
_DENIALS = (
    "dispatch_authorized", "automatic_replay_authorized",
    "consent_authenticated", "cross_store_atomicity_proven",
    "external_effect_verified", "trusted_clock_verified",
)
_SOURCE_DENIALS = (
    (_MEMORY, ("caller_commit_authenticated", "automatic_retry_authorized",
               "write_authorized", "trusted_clock_verified")),
    (_PLANNER, ("dispatch_authorized", "automatic_replay_authorized",
                "consent_authenticated", "cross_store_atomicity_proven",
                "external_outcome_verified")),
    (_ATOMIC, ("dispatch_authorized", "automatic_replay_authorized",
               "external_effect_verified", "independent_custody_verified",
               "manual_review_required")),
)
_SCHEMAS = tuple(
    (cls, tuple((name, vars(cls).get(name)) for name in
        fields + denials + ("__init__", "__new__", "__getattribute__", "__getattr__")))
    for cls, fields, denials in (
        (_MEMORY, _MEMORY_FIELDS, _SOURCE_DENIALS[0][1]),
        (_PLANNER, _PLANNER_FIELDS, _SOURCE_DENIALS[1][1]),
        (_ATOMIC, _ATOMIC_FIELDS, _SOURCE_DENIALS[2][1]),
        (_REPORT, _REPORT_FIELDS, _DENIALS + ("manual_review_required",)),
    )
)
_ORIGINAL_CODECS = (hashlib.sha256, json.dumps, re.compile)
_ORIGINAL_DOMAIN = _DOMAIN
_ORIGINAL_CONSTANTS = (
    _SHA, _OCC, _MAX_OCCURRENCES, _MAX_STEPS, _MEMORY_DISPOSITIONS,
    _ATOMIC_STATES,
)


def _protocol() -> None:
    if (
        (hashlib.sha256, json.dumps, re.compile) != _ORIGINAL_CODECS
        or _DOMAIN is not _ORIGINAL_DOMAIN
        or (_SHA, _OCC, _MAX_OCCURRENCES, _MAX_STEPS,
            _MEMORY_DISPOSITIONS, _ATOMIC_STATES) != _ORIGINAL_CONSTANTS
        or memory_module.MemoryAmbiguityPair is not _MEMORY
        or planner_module.DisconnectedPlannerSlotBridge is not _PLANNER
        or atomic_module.AtomicUnknownOutcomeReview is not _ATOMIC
        or DisconnectedRecoveryQuarantineInventory is not _REPORT
        or any(
            vars(cls).get(name) is not original
            for cls, fields in _SCHEMAS for name, original in fields
        )
    ):
        raise DisconnectedRecoveryInventoryRejected(
            "quarantine inventory protocol changed"
        )


def _sha(value: object) -> bool:
    return type(value) is str and _SHA.fullmatch(value) is not None


def _digest(domain: bytes, payload: object) -> str:
    raw = json.dumps(
        payload, ensure_ascii=True, separators=(",", ":"), allow_nan=False,
    ).encode("ascii")
    return hashlib.sha256(domain + raw).hexdigest()


def review_disconnected_recovery_quarantine(
    memory: MemoryAmbiguityPair,
    planner: DisconnectedPlannerSlotBridge,
    atomic_reports: tuple[AtomicUnknownOutcomeReview, ...],
) -> DisconnectedRecoveryQuarantineInventory:
    """Reject contradictory local receipts; ALWAYS retain manual quarantine."""
    _protocol()
    if (
        type(memory) is not _MEMORY or type(planner) is not _PLANNER
        or type(atomic_reports) is not tuple
        or not 1 <= len(atomic_reports) <= _MAX_OCCURRENCES
        or any(type(item) is not _ATOMIC for item in atomic_reports)
    ):
        raise DisconnectedRecoveryInventoryRejected(
            "exact bounded local recovery reports required"
        )

    def epoch() -> tuple[object, ...]:
        return (
            tuple(getattr(memory, name) for name in _MEMORY_FIELDS),
            tuple(getattr(planner, name) for name in _PLANNER_FIELDS),
            tuple(
                tuple(getattr(item, name) for name in _ATOMIC_FIELDS)
                for item in atomic_reports
            ),
        )

    original = epoch()
    mem, plan, atoms = original
    if (
        type(mem[0]) is not str or mem[0] not in _MEMORY_DISPOSITIONS
        or not all(_sha(x) for x in mem[1:])
        or mem[-1] != _digest(
            b"ARK-memory-ambiguous-dual-review-v1\0", mem[:-1],
        )
        or not all(_sha(x) for x in plan[:3])
        or type(plan[3]) is not tuple or type(plan[4]) is not tuple
        or not 1 <= len(plan[3]) <= _MAX_STEPS
        or not all(type(x) is str and x for x in plan[3])
        or plan[3] != tuple(sorted(set(plan[3])))
        or plan[4] != tuple(sorted(set(plan[4])))
        or not set(plan[4]).issubset(set(plan[3]))
        or type(plan[5]) is not int or not 0 <= plan[5] <= len(plan[3])
        or not _sha(plan[6])
        or plan[6] != _digest(
            b"ARK-disconnected-planner-slot-restart-bridge-v1\0", plan[:-1],
        )
    ):
        raise DisconnectedRecoveryInventoryRejected(
            "Memory or Planner receipt integrity mismatch"
        )
    names = []
    present = 0
    for occurrence, state, before, observed, exists in atoms:
        if (
            type(occurrence) is not str or _OCC.fullmatch(occurrence) is None
            or type(state) is not str or state not in _ATOMIC_STATES
            or type(before) is not int or type(observed) is not int
            or not 0 <= before <= observed <= 128
            or type(exists) is not bool
            or (state == "UNCHANGED" and (exists or observed != before))
            or (state == "LOCALLY_RECORDED"
                and (not exists or observed <= before))
            or (state == "PREEXISTING" and (not exists or before == 0))
            or (state == "ADVANCED_OTHER" and (exists or observed <= before))
        ):
            raise DisconnectedRecoveryInventoryRejected(
                "inconsistent local atomic occurrence state"
            )
        names.append(occurrence)
        present += exists
    if names != sorted(set(names)):
        raise DisconnectedRecoveryInventoryRejected(
            "duplicate or unordered local occurrences"
        )

    def stable() -> None:
        _protocol()
        if epoch() != original:
            raise DisconnectedRecoveryInventoryRejected(
                "recovery receipts changed during aggregation"
            )
        for report, (_, flags) in (
            (memory, _SOURCE_DENIALS[0]),
            (planner, _SOURCE_DENIALS[1]),
            *((item, _SOURCE_DENIALS[2]) for item in atomic_reports),
        ):
            for flag in flags:
                expected = flag == "manual_review_required"
                if getattr(report, flag) is not expected:
                    raise DisconnectedRecoveryInventoryRejected(
                        "local recovery report acquired authority"
                    )

    stable()
    quarantined = (
        bool(plan[4]) or mem[0] != "LOCAL_UNCHANGED_REVIEW"
        or any(state != "UNCHANGED" for _, state, _, _, _ in atoms)
    )
    disposition = "QUARANTINED" if quarantined else "MANUAL_REVIEW_REQUIRED"
    digest = _digest(_DOMAIN, (mem[-1], plan[-1], atoms, disposition))
    stable()
    report = _REPORT(
        plan[0], mem[0], len(plan[3]), len(plan[4]), len(atoms), present,
        disposition, digest,
    )
    _protocol()
    fields = (
        plan[0], mem[0], len(plan[3]), len(plan[4]), len(atoms), present,
        disposition, digest,
    )
    if (
        type(report) is not _REPORT
        or tuple(getattr(report, name) for name in _REPORT_FIELDS) != fields
        or report.manual_review_required is not True
        or any(getattr(report, name) is not False for name in _DENIALS)
    ):
        raise DisconnectedRecoveryInventoryRejected(
            "quarantine inventory acquired authority"
        )
    stable()
    if tuple(getattr(report, name) for name in _REPORT_FIELDS) != fields:
        raise DisconnectedRecoveryInventoryRejected(
            "quarantine inventory result changed"
        )
    return report
