"""Fail-closed bridge: recovered Planner DAG + durable synthetic WRITE slots.

This joins two independently reviewed local sources. It does NOT make their
reads atomic, authenticate the separate inventory, approve/replay a WRITE, or
produce evidence that an external side effect occurred.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass

from . import disconnected_restart_receipt_inventory_bundle as bundle_module
from . import disconnected_write_restart_binding as slot_module
from .contracts import Effect, StepState
from .disconnected_dependency_quarantine_projection import (
    DisconnectedDependencyClaim,
    DisconnectedDependencyProjection,
)
from .disconnected_write_recovery_fence import OfflineRecoveryStepClaim
from .disconnected_write_slot_ledger import (
    DisconnectedWriteSlotLedger,
    WriteSlotLedgerWitness,
)
from .planner_journal_review import SyntheticPlanRecovery, SyntheticPlanTail
from .synthetic_write_quarantine_matrix_review import SyntheticWriteStoreObservation

_DOMAIN = b"ARK-disconnected-planner-slot-restart-bridge-v1\0"
_MAX_STEPS = 24
_MAX_STEP_ID_BYTES = 256  # Local review budget; not a frozen Planner ID limit.
_ORIGINAL_CODECS = (hashlib.sha256, json.dumps)
_ORIGINAL_REVIEWERS = (
    bundle_module.review_disconnected_restart_receipt_bundle,
    slot_module.review_disconnected_write_restart,
)


class DisconnectedPlannerSlotBridgeRejected(ValueError):
    """Recovered Planner and durable slot inventory cannot be joined safely."""


@dataclass(frozen=True, slots=True)
class DisconnectedPlannerSlotBridge:
    plan_id: str
    bundle_sha256: str
    slot_fingerprint: str
    held_step_ids: tuple[str, ...]
    unknown_step_ids: tuple[str, ...]
    reserved_write_count: int
    bridge_sha256: str

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
    def external_outcome_verified(self) -> bool:
        return False


_RESULT = DisconnectedPlannerSlotBridge
_FIELDS = (
    "plan_id", "bundle_sha256", "slot_fingerprint", "held_step_ids",
    "unknown_step_ids", "reserved_write_count", "bridge_sha256",
    "__init__", "__new__", "__getattribute__", "__getattr__",
    "dispatch_authorized", "automatic_replay_authorized",
    "consent_authenticated", "cross_store_atomicity_proven",
    "external_outcome_verified",
)
_ORIGINAL_RESULT = tuple(vars(_RESULT).get(name) for name in _FIELDS)


def _valid_step_id(value: object) -> bool:
    """Reject forged inputs before dict/set/equality or journal/SQLite callbacks."""
    if type(value) is not str or not value or "\x00" in value:
        return False
    try:
        return len(value.encode("utf-8", errors="strict")) <= _MAX_STEP_ID_BYTES
    except UnicodeError:
        return False


_ORIGINAL_STEP_ID_CHECK = _valid_step_id

# Reject a class-level slot/getter substitution before inspecting private
# Planner IDs or asking either independent child reviewer to open SQLite.
# A frozen dataclass instance does not make its class descriptors immutable.
# This is process-local callback custody, NOT durable plan authentication.
_INPUT_TYPES = (
    DisconnectedDependencyClaim,
    DisconnectedDependencyProjection,
    OfflineRecoveryStepClaim,
    SyntheticWriteStoreObservation,
    SyntheticPlanRecovery,
    SyntheticPlanTail,
    WriteSlotLedgerWitness,
)
_INPUT_FIELD_NAMES = (
    ("step_id", "effect", "state", "depends_on"),
    ("topology_digest", "matrix_digest", "holds", "digest"),
    ("step_id", "effect", "state", "depends_on",
     "result_sha256", "reservation_id"),
    ("step_id", "plan_state", "reservation", "preaction_audit", "audit_link"),
    ("tail", "step_statuses", "ambiguous_running_steps"),
    ("topology_digest", "event_count", "event_hash", "status_digest",
     "last_at_ms"),
    ("count", "chain_sha256"),
)
_INPUT_HOOKS = ("__getattribute__", "__getattr__", "__init__", "__new__")
_INPUT_DESCRIPTORS = tuple(
    tuple(vars(cls).get(name) for name in (*fields, *_INPUT_HOOKS))
    for cls, fields in zip(_INPUT_TYPES, _INPUT_FIELD_NAMES, strict=True)
)


def _protocol() -> None:
    if (
        _DOMAIN != b"ARK-disconnected-planner-slot-restart-bridge-v1\0"
        or type(_MAX_STEPS) is not int or _MAX_STEPS != 24
        or type(_MAX_STEP_ID_BYTES) is not int or _MAX_STEP_ID_BYTES != 256
        or _valid_step_id is not _ORIGINAL_STEP_ID_CHECK
        or any(
            now is not original
            for now, original in zip(
                (
                    DisconnectedDependencyClaim, DisconnectedDependencyProjection,
                    OfflineRecoveryStepClaim, SyntheticWriteStoreObservation,
                    SyntheticPlanRecovery, SyntheticPlanTail, WriteSlotLedgerWitness,
                ), _INPUT_TYPES, strict=True,
            )
        )
        or any(
            any(
                current is not original
                for current, original in zip(
                    (vars(cls).get(name) for name in (*fields, *_INPUT_HOOKS)),
                    originals, strict=True,
                )
            )
            for cls, fields, originals in zip(
                _INPUT_TYPES, _INPUT_FIELD_NAMES, _INPUT_DESCRIPTORS,
                strict=True,
            )
        )
        or any(
            current is not original
            for current, original in zip(
                (hashlib.sha256, json.dumps), _ORIGINAL_CODECS, strict=True,
            )
        )
        or any(
            current is not original
            for current, original in zip(
                (
                    bundle_module.review_disconnected_restart_receipt_bundle,
                    slot_module.review_disconnected_write_restart,
                ), _ORIGINAL_REVIEWERS, strict=True,
            )
        )
        or DisconnectedPlannerSlotBridge is not _RESULT
        or any(vars(_RESULT).get(name) is not old for name, old in zip(
            _FIELDS, _ORIGINAL_RESULT, strict=True,
        ))
    ):
        raise DisconnectedPlannerSlotBridgeRejected("restart bridge protocol changed")


def review_disconnected_planner_slot_restart(
    *,
    ledger: DisconnectedWriteSlotLedger,
    retained_slot_witness: WriteSlotLedgerWitness,
    recovered: SyntheticPlanRecovery,
    retained_tail: SyntheticPlanTail,
    claims: tuple[DisconnectedDependencyClaim, ...],
    independently_expected_write_ids: tuple[str, ...],
    observations: tuple[SyntheticWriteStoreObservation, ...],
    dependency: DisconnectedDependencyProjection,
    offline_steps: tuple[OfflineRecoveryStepClaim, ...],
) -> DisconnectedPlannerSlotBridge:
    """Verify complete local WRITE slot membership without granting authority.

    This intentionally supports only <=24 synthetic steps with a plan identity
    identical to the retained topology digest. A real independent plan/slot
    identity attestation and a cross-store transactional snapshot remain open.
    """
    _protocol()
    if (
        type(ledger) is not DisconnectedWriteSlotLedger
        or type(retained_slot_witness) is not WriteSlotLedgerWitness
        or type(recovered) is not SyntheticPlanRecovery
        or type(retained_tail) is not SyntheticPlanTail
        or type(dependency) is not DisconnectedDependencyProjection
        or type(claims) is not tuple
        or type(offline_steps) is not tuple
        or type(independently_expected_write_ids) is not tuple
        or type(observations) is not tuple
        or len(independently_expected_write_ids) > _MAX_STEPS
        or any(not _valid_step_id(step_id)
               for step_id in independently_expected_write_ids)
        or not 1 <= len(claims) <= _MAX_STEPS
        or len(offline_steps) != len(claims)
        or any(type(item) is not DisconnectedDependencyClaim for item in claims)
        or any(type(item) is not OfflineRecoveryStepClaim for item in offline_steps)
        or any(not _valid_step_id(item.step_id) for item in claims)
        or any(not _valid_step_id(item.step_id) for item in offline_steps)
        or any(
            type(item) is not SyntheticWriteStoreObservation
            or not _valid_step_id(item.step_id)
            for item in observations
        )
    ):
        raise DisconnectedPlannerSlotBridgeRejected("inexact restart bridge inputs")

    # Exact bounded string admission now also covers reflected claim/offline/
    # observation IDs before any dict key, set, sort, or journal/SQLite callback.
    # Forged str subclasses must not execute their __hash__ or __eq__.
    # Reconcile the complete ordered offline step inventory against every
    # canonical recovered Planner step, not merely the reserved subset.
    expected = {
        step.step_id: (step.effect.value.upper(), step.state.value.upper(),
                       step.depends_on)
        for step in claims
        if type(step.effect) is Effect and type(step.state) is StepState
    }
    if len(expected) != len(claims):
        raise DisconnectedPlannerSlotBridgeRejected("invalid Planner identity inventory")
    observed = {}
    for step in offline_steps:
        if step.step_id in observed:
            raise DisconnectedPlannerSlotBridgeRejected("duplicate offline step")
        observed[step.step_id] = step
    if set(expected) != set(observed):
        raise DisconnectedPlannerSlotBridgeRejected("offline step inventory mismatch")
    for name, (effect, state, parents) in expected.items():
        offline = observed[name]
        if (
            offline.effect != effect or offline.depends_on != parents
            or (
                offline.state != state
                and not (state == "RUNNING" and offline.state == "UNKNOWN")
            )
        ):
            raise DisconnectedPlannerSlotBridgeRejected("Planner/offline state mismatch")
    if tuple(sorted(
        name for name, (effect, _, _) in expected.items() if effect == "WRITE"
    )) != independently_expected_write_ids:
        raise DisconnectedPlannerSlotBridgeRejected("WRITE inventory mismatch")
    # The synthetic cross-store matrix is caller supplied. Its reservation
    # observation must agree with the independently opened durable slot ledger
    # claim; otherwise a fake "present" can be accepted with zero real slots.
    for observation in observations:
        if (
            type(observation) is not SyntheticWriteStoreObservation
            or observation.step_id not in expected
            or expected[observation.step_id][0] != "WRITE"
            or observation.plan_state != expected[observation.step_id][1].lower()
            or observation.reservation not in ("present", "absent")
            or (observation.reservation == "present")
            != (observed[observation.step_id].reservation_id is not None)
        ):
            raise DisconnectedPlannerSlotBridgeRejected(
                "synthetic reservation observation disagrees with slot claim"
            )
    plan_id = retained_tail.topology_digest
    # The two child reviewers run in separate epochs. In particular the
    # durable SQLite reviewer can invoke reentrant callbacks *after* the
    # Planner reviewer has produced its receipt. Pin all Planner-side input
    # carriers before either callback, not only offline_steps. A mutable
    # frozen dataclass field is not independent historical evidence.
    def source_epoch() -> tuple[object, ...]:
        return (
            (id(ledger), id(ledger._path), id(retained_slot_witness),
             id(retained_slot_witness.count),
             id(retained_slot_witness.chain_sha256)),
            (id(recovered), id(recovered.tail), id(recovered.step_statuses),
             id(recovered.ambiguous_running_steps)),
            (id(retained_tail), id(retained_tail.topology_digest),
             id(retained_tail.event_count), id(retained_tail.event_hash),
             id(retained_tail.status_digest), id(retained_tail.last_at_ms)),
            tuple(
                (id(step), id(step.step_id), id(step.effect),
                 id(step.state), id(step.depends_on))
                for step in claims
            ),
            id(independently_expected_write_ids),
            tuple(id(name) for name in independently_expected_write_ids),
            tuple(
                (id(row), id(row.step_id), id(row.plan_state),
                 id(row.reservation), id(row.preaction_audit),
                 id(row.audit_link))
                for row in observations
            ),
            (id(dependency), id(dependency.topology_digest),
             id(dependency.matrix_digest), id(dependency.holds),
             id(dependency.digest)),
            tuple(
                (id(hold), id(hold.step_id), id(hold.reason))
                for hold in dependency.holds
            ),
        )

    original_source_epoch = source_epoch()
    initial_offline = tuple(
        (step, step.step_id, step.effect, step.state, step.depends_on,
         step.result_sha256, step.reservation_id)
        for step in offline_steps
    )

    def stable() -> None:
        _protocol()
        if source_epoch() != original_source_epoch:
            raise DisconnectedPlannerSlotBridgeRejected(
                "Planner source carriers changed between independent reviews"
            )
        if any(
            type(item) is not OfflineRecoveryStepClaim or item is not old
            or (
                item.step_id, item.effect, item.state, item.depends_on,
                item.result_sha256, item.reservation_id,
            ) != (name, effect, state, parents, result, reservation)
            for item, name, effect, state, parents, result, reservation
            in initial_offline for old in (item,)
        ):
            raise DisconnectedPlannerSlotBridgeRejected("offline step mutated")

    stable()
    try:
        bundle = bundle_module.review_disconnected_restart_receipt_bundle(
            recovered=recovered,
            retained_tail=retained_tail,
            claims=claims,
            independently_expected_write_ids=independently_expected_write_ids,
            observations=observations,
            dependency=dependency,
        )
        stable()
        slot = slot_module.review_disconnected_write_restart(
            ledger, retained_slot_witness, plan_id, offline_steps,
        )
    except (
        bundle_module.DisconnectedRestartReceiptBundleRejected,
        slot_module.OfflineWriteRestartRejected,
    ) as exc:
        raise DisconnectedPlannerSlotBridgeRejected(
            "restart source review rejected"
        ) from exc
    stable()

    if (
        type(bundle) is not bundle_module.DisconnectedRestartReceiptBundle
        or type(slot) is not slot_module.OfflineWriteRestartReport
        or bundle.topology_digest != plan_id
        or slot.plan_id != plan_id
        or slot.total_steps != len(claims)
        or slot.reserved_write_steps > len(independently_expected_write_ids)
        or slot.quarantined_write_steps != len(independently_expected_write_ids)
        or bundle.held_step_ids != tuple(sorted(expected))
        or tuple(sorted(bundle.unknown_step_ids)) != bundle.unknown_step_ids
        or any(getattr(bundle, flag) is not False for flag in (
            "dispatch_authorized", "automatic_replay_authorized",
            "independent_inventory_verified", "external_outcome_verified",
        ))
        or any(getattr(slot, flag) is not False for flag in (
            "tool_dispatch_authorized", "write_replay_authorized",
            "external_outcome_verified", "trusted_clock_verified",
            "consent_verified", "cross_store_atomicity_proven",
        ))
    ):
        raise DisconnectedPlannerSlotBridgeRejected("restart receipts disagree")

    encoded = json.dumps(
        (
            plan_id, bundle.bundle_sha256, slot.fingerprint,
            bundle.held_step_ids, bundle.unknown_step_ids,
            slot.reserved_write_steps,
        ),
        ensure_ascii=True, separators=(",", ":"), allow_nan=False,
    ).encode("ascii")
    digest = hashlib.sha256(_DOMAIN + encoded).hexdigest()
    stable()
    result = _RESULT(
        plan_id, bundle.bundle_sha256, slot.fingerprint,
        bundle.held_step_ids, bundle.unknown_step_ids,
        slot.reserved_write_steps, digest,
    )
    if (
        type(result) is not _RESULT
        or result.bridge_sha256 != digest
        or any(getattr(result, flag) is not False for flag in (
            "dispatch_authorized", "automatic_replay_authorized",
            "consent_authenticated", "cross_store_atomicity_proven",
            "external_outcome_verified",
        ))
    ):
        raise DisconnectedPlannerSlotBridgeRejected("restart bridge gained authority")
    stable()
    return result
