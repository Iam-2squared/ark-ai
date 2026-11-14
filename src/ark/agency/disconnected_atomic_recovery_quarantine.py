"""Read-only quarantine of registry-bound synthetic pre-action occurrences.

A valid local SQLite receipt is not authenticated consent, independent custody,
an external effect or permission to replay. This adapter never reserves an
occurrence or exposes ToolBackend execution.
"""

from __future__ import annotations

from dataclasses import dataclass

from .contracts import ToolCall
from .disconnected_atomic_preaction_ledger import (
    AtomicPreactionRejected,
    AtomicPreactionSnapshot,
    AtomicPreactionWitness,
    DisconnectedAtomicPreactionLedger,
    _witness_image,
)
from .disconnected_atomic_registry_bridge import derive_registered_atomic_intent
from .registry import ToolRegistry

_SNAPSHOT_TYPE = AtomicPreactionSnapshot
_SNAPSHOT_DENIALS = (
    "tool_dispatch_authorized",
    "automatic_replay_authorized",
    "external_effect_proven",
    "trusted_approval_verified",
    "independent_custody_proven",
)
_ORIGINAL_DENIALS = tuple(vars(_SNAPSHOT_TYPE)[name] for name in _SNAPSHOT_DENIALS)


class AtomicRecoveryQuarantineRejected(ValueError):
    """Retained pre-action and registry evidence cannot be safely compared."""


@dataclass(frozen=True, slots=True)
class AtomicRecoveryQuarantine:
    """Only a local occurrence-membership observation, never a WRITE approval."""

    occurrence_id: str
    locally_recorded: bool
    retained_count: int

    @property
    def binding_proven(self) -> bool:
        return False

    @property
    def tool_dispatch_authorized(self) -> bool:
        return False

    @property
    def automatic_replay_authorized(self) -> bool:
        return False

    @property
    def external_effect_proven(self) -> bool:
        return False

    @property
    def independent_custody_proven(self) -> bool:
        return False

    @property
    def manual_review_required(self) -> bool:
        return True


# A local SQLite witness cannot authenticate an action, but replaced
# review callbacks and result descriptors must not acquire dispatch authority.
_SNAPSHOT_FIELDS = ("witness", "occurrence_ids")
_CARRIER_HOOKS = ("__init__", "__new__", "__getattribute__", "__getattr__")
_ORIGINAL_SNAPSHOT_FIELDS = tuple(
    vars(_SNAPSHOT_TYPE).get(name) for name in _SNAPSHOT_FIELDS
)
_ORIGINAL_SNAPSHOT_HOOKS = tuple(
    vars(_SNAPSHOT_TYPE).get(name) for name in _CARRIER_HOOKS
)
_ORIGINAL_SNAPSHOT_NAMES = _SNAPSHOT_DENIALS
_ORIGINAL_SNAPSHOT_DESCRIPTORS = _ORIGINAL_DENIALS
_RESULT_TYPE = AtomicRecoveryQuarantine
_RESULT_FIELDS = ("occurrence_id", "locally_recorded", "retained_count")
_RESULT_DENIALS = (
    "binding_proven", "tool_dispatch_authorized", "automatic_replay_authorized",
    "external_effect_proven", "independent_custody_proven",
    "manual_review_required",
)
_ORIGINAL_RESULT_NAMES = _RESULT_DENIALS
_ORIGINAL_RESULT_DESCRIPTORS = tuple(
    vars(_RESULT_TYPE).get(name) for name in (*_RESULT_FIELDS, *_RESULT_DENIALS)
)
_ORIGINAL_RESULT_HOOKS = tuple(
    vars(_RESULT_TYPE).get(name) for name in _CARRIER_HOOKS
)
_ORIGINAL_DERIVE = derive_registered_atomic_intent
_ORIGINAL_INSPECT = vars(DisconnectedAtomicPreactionLedger).get("inspect")
_ORIGINAL_WITNESS_IMAGE = _witness_image
_WITNESS_TYPE = AtomicPreactionWitness
_WITNESS_FIELDS = ("count", "tip_sha256")
_ORIGINAL_WITNESS_FIELDS = tuple(
    vars(_WITNESS_TYPE).get(name) for name in _WITNESS_FIELDS
)
_ORIGINAL_WITNESS_HOOKS = tuple(
    vars(_WITNESS_TYPE).get(name) for name in _CARRIER_HOOKS
)


def _original_snapshot_denials() -> None:
    if (
        _SNAPSHOT_DENIALS is not _ORIGINAL_SNAPSHOT_NAMES
        or _ORIGINAL_DENIALS is not _ORIGINAL_SNAPSHOT_DESCRIPTORS
        or _RESULT_DENIALS is not _ORIGINAL_RESULT_NAMES
        or derive_registered_atomic_intent is not _ORIGINAL_DERIVE
        or vars(DisconnectedAtomicPreactionLedger).get("inspect") is not _ORIGINAL_INSPECT
        or _witness_image is not _ORIGINAL_WITNESS_IMAGE
        or AtomicPreactionWitness is not _WITNESS_TYPE
        or any(
            vars(_WITNESS_TYPE).get(name) is not original
            for names, originals in (
                (_WITNESS_FIELDS, _ORIGINAL_WITNESS_FIELDS),
                (_CARRIER_HOOKS, _ORIGINAL_WITNESS_HOOKS),
            )
            for name, original in zip(names, originals, strict=True)
        )
        or AtomicRecoveryQuarantine is not _RESULT_TYPE
        or any(
            vars(_SNAPSHOT_TYPE).get(name) is not original
            for names, originals in (
                (_SNAPSHOT_FIELDS, _ORIGINAL_SNAPSHOT_FIELDS),
                (_CARRIER_HOOKS, _ORIGINAL_SNAPSHOT_HOOKS),
            )
            for name, original in zip(names, originals, strict=True)
        )
        or any(
            vars(_RESULT_TYPE).get(name) is not original
            for name, original in zip(
                (*_RESULT_FIELDS, *_RESULT_DENIALS),
                _ORIGINAL_RESULT_DESCRIPTORS, strict=True,
            )
        )
        or any(
            vars(_RESULT_TYPE).get(name) is not original
            for name, original in zip(
                _CARRIER_HOOKS, _ORIGINAL_RESULT_HOOKS, strict=True,
            )
        )
        or AtomicPreactionSnapshot is not _SNAPSHOT_TYPE
        or any(
            vars(_SNAPSHOT_TYPE).get(name) is not original
            for name, original in zip(_SNAPSHOT_DENIALS, _ORIGINAL_DENIALS, strict=True)
        )
    ):
        raise AtomicRecoveryQuarantineRejected(
            "local pre-action authority definition changed"
        )


def review_registered_atomic_recovery(
    ledger: DisconnectedAtomicPreactionLedger,
    retained: AtomicPreactionWitness,
    registry: ToolRegistry,
    call: ToolCall,
    *,
    occurrence_id: str,
) -> AtomicRecoveryQuarantine:
    """Quarantine either local outcome; never infer the registered action from ID.

    Ledger.inspect() confirms a *retained local* count/tip and internal audit,
    not an independent witness. Its occurrence-only projection cannot prove
    the bound_action_id or request digest matched this registered call.
    """
    _original_snapshot_denials()
    if (
        type(ledger) is not DisconnectedAtomicPreactionLedger
        or type(retained) is not AtomicPreactionWitness
        or type(registry) is not ToolRegistry
        or type(call) is not ToolCall
    ):
        raise AtomicRecoveryQuarantineRejected("exact recovery inputs required")
    try:
        # Retain exact scalar witness values before any registry callback or
        # SQLite access. Dataclass equality is mutable and can be forged.
        prior = _witness_image(retained)
        _original_snapshot_denials()
        claim = derive_registered_atomic_intent(
            registry, call, occurrence_id=occurrence_id,
        )
        _original_snapshot_denials()
        bound_occurrence = claim.occurrence_id
        snapshot = ledger.inspect(retained)
        _original_snapshot_denials()
        if (
            type(snapshot) is not _SNAPSHOT_TYPE
            or type(snapshot.witness) is not _WITNESS_TYPE
            or _witness_image(retained) != prior
            or _witness_image(snapshot.witness) != prior
            or type(snapshot.occurrence_ids) is not tuple
            or len(snapshot.occurrence_ids) != prior[0]
            or len(set(snapshot.occurrence_ids)) != prior[0]
            or claim.occurrence_id is not bound_occurrence
        ):
            raise AtomicRecoveryQuarantineRejected("local recovery snapshot invalid")
        for name in _SNAPSHOT_DENIALS:
            _original_snapshot_denials()
            if getattr(snapshot, name) is not False:
                raise AtomicRecoveryQuarantineRejected(
                    "local recovery snapshot acquired authority"
                )
            if _witness_image(retained) != prior:
                raise AtomicRecoveryQuarantineRejected(
                    "retained witness changed during recovery review"
                )
        _original_snapshot_denials()
        # Membership is not proof that the stored bound action/request matched.
        recorded = bound_occurrence in snapshot.occurrence_ids
        result = _RESULT_TYPE(bound_occurrence, recorded, prior[0])
        _original_snapshot_denials()
        if (
            type(result) is not _RESULT_TYPE
            or result.occurrence_id is not bound_occurrence
            or type(result.locally_recorded) is not bool
            or result.locally_recorded is not recorded
            or type(result.retained_count) is not int
            or result.retained_count != prior[0]
            or _witness_image(retained) != prior
        ):
            raise AtomicRecoveryQuarantineRejected("local recovery result changed")
        for name in _RESULT_DENIALS:
            if getattr(result, name) is not (name == "manual_review_required"):
                raise AtomicRecoveryQuarantineRejected("local recovery result acquired authority")
            _original_snapshot_denials()
            if _witness_image(retained) != prior:
                raise AtomicRecoveryQuarantineRejected(
                    "retained witness changed during recovery result checks"
                )
        return result
    except AtomicPreactionRejected as exc:
        raise AtomicRecoveryQuarantineRejected(
            "local recovery is stale, malformed or registry-unbound"
        ) from exc
