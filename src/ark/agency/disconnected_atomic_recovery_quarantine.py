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


def _original_snapshot_denials() -> None:
    if (
        AtomicPreactionSnapshot is not _SNAPSHOT_TYPE
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
        claim = derive_registered_atomic_intent(
            registry, call, occurrence_id=occurrence_id,
        )
        _original_snapshot_denials()
        snapshot = ledger.inspect(retained)
        _original_snapshot_denials()
        if (
            type(snapshot) is not _SNAPSHOT_TYPE
            or type(snapshot.witness) is not AtomicPreactionWitness
            or snapshot.witness != retained
            or type(snapshot.occurrence_ids) is not tuple
            or len(snapshot.occurrence_ids) != retained.count
            or len(set(snapshot.occurrence_ids)) != retained.count
        ):
            raise AtomicRecoveryQuarantineRejected("local recovery snapshot invalid")
        for name in _SNAPSHOT_DENIALS:
            _original_snapshot_denials()
            if getattr(snapshot, name) is not False:
                raise AtomicRecoveryQuarantineRejected(
                    "local recovery snapshot acquired authority"
                )
        _original_snapshot_denials()
        # Membership is not proof that the stored bound action/request matched.
        recorded = claim.occurrence_id in snapshot.occurrence_ids
        return AtomicRecoveryQuarantine(claim.occurrence_id, recorded, retained.count)
    except AtomicPreactionRejected as exc:
        raise AtomicRecoveryQuarantineRejected(
            "local recovery is stale, malformed or registry-unbound"
        ) from exc
