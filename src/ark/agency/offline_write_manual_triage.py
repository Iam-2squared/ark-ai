"""Operator-facing, read-only queue for ambiguous disconnected WRITE claims.

This is a *manual investigation checklist*, not a user approval, a
human-reviewed outcome, or a permission to retry an unknown external effect.
It binds the existing synthetic recovery fence to a local reservation review.
"""

from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass

from .disconnected_write_recovery_fence import (
    OfflineRecoveryStepClaim,
    review_disconnected_recovery_fence,
)
from .disconnected_write_restart_binding import (
    OfflineWriteRestartReport,
    review_disconnected_write_restart,
)
from .disconnected_write_slot_ledger import (
    DisconnectedWriteSlotLedger,
    WriteSlotLedgerWitness,
)

_SHA = re.compile(r"[0-9a-f]{64}\Z")
_DOMAIN = b"ARK-detached-manual-WRITE-triage-v1\0"


class OfflineWriteTriageRejected(ValueError):
    """The supplied synthetic recovery evidence cannot be reconciled."""


@dataclass(frozen=True, slots=True)
class OfflineWriteTriageItem:
    step_id: str
    claimed_state: str
    disposition: str
    reservation_id: str | None
    investigation: str


@dataclass(frozen=True, slots=True)
class OfflineWriteTriagePacket:
    plan_id: str
    items: tuple[OfflineWriteTriageItem, ...]
    reservation_chain_sha256: str
    recovery_fingerprint: str
    packet_sha256: str

    @property
    def human_review_completed(self) -> bool:
        return False

    @property
    def external_outcome_verified(self) -> bool:
        return False

    @property
    def dispatch_authorized(self) -> bool:
        return False

    @property
    def automatic_replay_authorized(self) -> bool:
        return False


_ITEM_TYPE = OfflineWriteTriageItem
_PACKET_TYPE = OfflineWriteTriagePacket
_RESTART_TYPE = OfflineWriteRestartReport
_STEP_TYPE = OfflineRecoveryStepClaim


def build_offline_write_triage_packet(
    ledger: DisconnectedWriteSlotLedger,
    retained: WriteSlotLedgerWitness,
    plan_id: str,
    steps: tuple[OfflineRecoveryStepClaim, ...],
) -> OfflineWriteTriagePacket:
    """List all WRITE claims without changing state or interpreting human consent.

    Unknown/RUNNING WRITE is always held for external-outcome investigation.
    A claimed SUCCEEDED WRITE is still unverified and never becomes automatic
    dispatch permission. READ steps are omitted from the operator checklist.
    """
    if (
        type(ledger) is not DisconnectedWriteSlotLedger
        or type(retained) is not WriteSlotLedgerWitness
        or type(plan_id) is not str
        or type(steps) is not tuple
        or not 1 <= len(steps) <= 24
        or any(type(step) is not _STEP_TYPE for step in steps)
    ):
        raise OfflineWriteTriageRejected("exact bounded local recovery inputs required")
    original_steps = tuple(steps)
    saved = tuple((
        item.step_id, item.effect, item.depends_on, item.state,
        item.result_sha256, item.reservation_id,
    ) for item in original_steps)
    original_path = ledger._path
    original_plan = plan_id
    previous_count, previous_chain = retained.count, retained.chain_sha256

    def stable() -> None:
        if (
            ledger._path is not original_path
            or plan_id is not original_plan
            or steps is not original_steps
            or type(retained) is not WriteSlotLedgerWitness
            or retained.count is not previous_count
            or retained.chain_sha256 is not previous_chain
            or len(steps) != len(original_steps)
        ):
            raise OfflineWriteTriageRejected("recovery inputs changed")
        for now, original, fields in zip(steps, original_steps, saved, strict=True):
            if (
                now is not original
                or any(a is not b for a, b in zip((
                    now.step_id, now.effect, now.depends_on, now.state,
                    now.result_sha256, now.reservation_id,
                ), fields, strict=True))
            ):
                raise OfflineWriteTriageRejected("recovery step epoch changed")

    stable()
    try:
        recovery = review_disconnected_write_restart(ledger, retained, plan_id, steps)
        stable()
        fence = review_disconnected_recovery_fence(plan_id, steps)
        stable()
    except (ValueError, TypeError, AttributeError) as exc:
        raise OfflineWriteTriageRejected("local WRITE recovery validation denied") from exc
    if (
        type(recovery) is not _RESTART_TYPE
        or recovery.plan_id is not plan_id
        or recovery.total_steps != len(steps)
        or type(recovery.fingerprint) is not str
        or _SHA.fullmatch(recovery.fingerprint) is None
        or recovery.tool_dispatch_authorized is not False
        or recovery.write_replay_authorized is not False
        or recovery.external_outcome_verified is not False
        or recovery.trusted_clock_verified is not False
        or recovery.consent_verified is not False
        or recovery.cross_store_atomicity_proven is not False
        or len(fence.decisions) != len(steps)
    ):
        raise OfflineWriteTriageRejected("local recovery proof gained authority")
    packet_items = []
    for fields, decision in zip(saved, fence.decisions, strict=True):
        step_id, effect, _, state, _, reservation = fields
        if decision.step_id != step_id:
            raise OfflineWriteTriageRejected("recovery disposition step mismatch")
        if effect != "WRITE":
            continue
        if decision.code == "READY_MOCK_ONLY":
            raise OfflineWriteTriageRejected("WRITE was released from quarantine")
        investigation = (
            "UNKNOWN_EFFECT_HOLD"
            if state in {"RUNNING", "UNKNOWN"}
            else "CLAIMED_OUTCOME_REVIEW_ONLY"
        )
        packet_items.append(_ITEM_TYPE(
            step_id, state, decision.code, reservation, investigation,
        ))
        stable()
    if recovery.reserved_write_steps != sum(
        item.reservation_id is not None for item in packet_items
    ):
        raise OfflineWriteTriageRejected("durable reservation coverage changed")
    pinned = tuple(packet_items)
    encoded = json.dumps(
        (plan_id, previous_count, previous_chain, recovery.fingerprint,
         [(i.step_id, i.claimed_state, i.disposition, i.reservation_id, i.investigation)
          for i in pinned]),
        separators=(",", ":"), ensure_ascii=True,
    ).encode("ascii")
    if len(encoded) > 24_576:
        raise OfflineWriteTriageRejected("operator packet metadata budget exceeded")
    fingerprint = hashlib.sha256(_DOMAIN + encoded).hexdigest()
    stable()
    packet = _PACKET_TYPE(plan_id, pinned, previous_chain, recovery.fingerprint, fingerprint)
    if (
        type(packet) is not _PACKET_TYPE
        or packet.plan_id is not plan_id
        or packet.items is not pinned
        or packet.reservation_chain_sha256 is not previous_chain
        or packet.recovery_fingerprint is not recovery.fingerprint
        or packet.packet_sha256 is not fingerprint
        or packet.human_review_completed is not False
        or packet.external_outcome_verified is not False
        or packet.dispatch_authorized is not False
        or packet.automatic_replay_authorized is not False
    ):
        raise OfflineWriteTriageRejected("operator packet acquired authority")
    stable()
    if (
        packet.plan_id is not plan_id
        or packet.items is not pinned
        or packet.packet_sha256 is not fingerprint
        or any(type(item) is not _ITEM_TYPE for item in packet.items)
    ):
        raise OfflineWriteTriageRejected("operator packet changed after authority check")
    return packet
