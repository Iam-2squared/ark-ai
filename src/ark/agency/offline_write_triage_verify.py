"""Detached integrity check for a manual-only UNKNOWN WRITE checklist.

This validator reads no ledger, executes no tool and grants no authority.
It checks that caller-controlled packet fields still match the supplied
caller-controlled retained witness. Neither is independently authenticated.
"""

from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass

from .disconnected_write_slot_ledger import (
    WriteSlotLedgerRejected,
    WriteSlotLedgerWitness,
    _check_witness,
)
from .offline_write_manual_triage import (
    OfflineWriteTriageItem,
    OfflineWriteTriagePacket,
)

_PLAN = re.compile(r"plan_[0-9a-f]{64}\Z")
_STEP = re.compile(r"step_[0-9a-f]{16}\Z")
_SLOT = re.compile(r"slot_[0-9a-f]{64}\Z")
_SHA = re.compile(r"[0-9a-f]{64}\Z")
_DOMAIN = b"ARK-detached-manual-WRITE-triage-v1\0"
_PENDING_CODES = frozenset((
    "QUARANTINE_RESERVED_WRITE", "HOLD_TERMINAL",
    "HOLD_UNCERTAIN", "WAIT_DEPENDENCY", "HELD_WRITE_APPROVAL",
))
_TERMINAL_STATES = frozenset(("FAILED", "CANCELLED", "BLOCKED"))


class OfflineWriteTriageVerificationRejected(ValueError):
    """A detached synthetic WRITE checklist is inconsistent or has gained authority."""


@dataclass(frozen=True, slots=True)
class OfflineWriteTriageVerification:
    plan_id: str
    item_count: int
    packet_sha256: str
    retained_count: int

    @property
    def independently_authenticated(self) -> bool:
        return False

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


_PACKET = OfflineWriteTriagePacket
_ITEM = OfflineWriteTriageItem
_WITNESS = WriteSlotLedgerWitness
_RESULT = OfflineWriteTriageVerification


def _exact_match(value: object, pattern: re.Pattern[str]) -> bool:
    return type(value) is str and pattern.fullmatch(value) is not None


def verify_offline_write_triage_packet(
    packet: OfflineWriteTriagePacket,
    retained: WriteSlotLedgerWitness,
) -> OfflineWriteTriageVerification:
    """Recompute an inert display packet from exact typed metadata and witness.

    Checking this checksum cannot prove a real-world effect, authenticate a
    human, or permit retries. A recomputed checksum can still be forged by a
    writer controlling both the packet and the separately supplied witness.
    """
    if type(packet) is not _PACKET or type(retained) is not _WITNESS:
        raise OfflineWriteTriageVerificationRejected("exact detached packet required")
    try:
        _check_witness(retained)
    except WriteSlotLedgerRejected as exc:
        raise OfflineWriteTriageVerificationRejected("invalid retained witness") from exc

    plan = packet.plan_id
    items = packet.items
    chain = packet.reservation_chain_sha256
    recovery = packet.recovery_fingerprint
    supplied_hash = packet.packet_sha256
    count = retained.count
    retained_chain = retained.chain_sha256
    if (
        not _exact_match(plan, _PLAN)
        or type(items) is not tuple or len(items) > 24
        or not _exact_match(chain, _SHA) or chain != retained_chain
        or not _exact_match(recovery, _SHA)
        or not _exact_match(supplied_hash, _SHA)
        or any(type(item) is not _ITEM for item in items)
    ):
        raise OfflineWriteTriageVerificationRejected("invalid detached checklist fields")

    original_items = tuple(items)
    saved: list[tuple[str, str, str, str | None, str]] = []
    seen: set[str] = set()
    reservations: set[str] = set()
    for item in original_items:
        step, state, code, reservation, investigation = (
            item.step_id, item.claimed_state, item.disposition,
            item.reservation_id, item.investigation,
        )
        if (
            not _exact_match(step, _STEP) or step in seen
            or type(state) is not str or type(code) is not str
            or type(investigation) is not str
            or (reservation is not None and not _exact_match(reservation, _SLOT))
            or (reservation is not None and reservation in reservations)
        ):
            raise OfflineWriteTriageVerificationRejected("invalid detached WRITE item")
        if state in {"UNKNOWN", "RUNNING"}:
            correct = code == "QUARANTINE_WRITE_UNKNOWN"
            expected_investigation = "UNKNOWN_EFFECT_HOLD"
        elif state == "SUCCEEDED":
            correct = code == "COMPLETE_UNVERIFIED"
            expected_investigation = "CLAIMED_OUTCOME_REVIEW_ONLY"
        elif state in _TERMINAL_STATES:
            correct = code == "TERMINAL"
            expected_investigation = "CLAIMED_OUTCOME_REVIEW_ONLY"
        elif state == "PENDING":
            correct = (
                code == "QUARANTINE_RESERVED_WRITE"
                if reservation is not None else code in _PENDING_CODES - {
                    "QUARANTINE_RESERVED_WRITE"
                }
            )
            expected_investigation = "CLAIMED_OUTCOME_REVIEW_ONLY"
        else:
            correct = False
            expected_investigation = ""
        if not correct or investigation != expected_investigation:
            raise OfflineWriteTriageVerificationRejected("unsafe WRITE disposition")
        seen.add(step)
        if reservation is not None:
            reservations.add(reservation)
        saved.append((step, state, code, reservation, investigation))

    def stable() -> None:
        if (
            type(packet) is not _PACKET or type(retained) is not _WITNESS
            or packet.plan_id is not plan or packet.items is not items
            or packet.reservation_chain_sha256 is not chain
            or packet.recovery_fingerprint is not recovery
            or packet.packet_sha256 is not supplied_hash
            or retained.count is not count
            or retained.chain_sha256 is not retained_chain
            or len(items) != len(original_items)
        ):
            raise OfflineWriteTriageVerificationRejected("detached packet epoch changed")
        for now, original, fields in zip(items, original_items, saved, strict=True):
            if (
                type(now) is not _ITEM or now is not original
                or any(current is not pinned for current, pinned in zip(
                    (now.step_id, now.claimed_state, now.disposition,
                     now.reservation_id, now.investigation),
                    fields, strict=True,
                ))
            ):
                raise OfflineWriteTriageVerificationRejected("detached item epoch changed")

    stable()
    encoded = json.dumps(
        (plan, count, retained_chain, recovery, saved),
        separators=(",", ":"), ensure_ascii=True,
    ).encode("ascii")
    if len(encoded) > 24_576:
        raise OfflineWriteTriageVerificationRejected("detached packet exceeds budget")
    expected_hash = hashlib.sha256(_DOMAIN + encoded).hexdigest()
    if supplied_hash != expected_hash:
        raise OfflineWriteTriageVerificationRejected("detached packet hash differs")
    stable()
    if (
        packet.human_review_completed is not False
        or packet.external_outcome_verified is not False
        or packet.dispatch_authorized is not False
        or packet.automatic_replay_authorized is not False
        or retained.independently_authenticated is not False
    ):
        raise OfflineWriteTriageVerificationRejected("detached packet acquired authority")
    stable()
    result = _RESULT(plan, len(items), supplied_hash, count)
    if (
        type(result) is not _RESULT
        or result.plan_id is not plan
        or result.item_count != len(items)
        or result.packet_sha256 is not supplied_hash
        or result.retained_count is not count
        or result.independently_authenticated is not False
        or result.human_review_completed is not False
        or result.external_outcome_verified is not False
        or result.dispatch_authorized is not False
        or result.automatic_replay_authorized is not False
    ):
        raise OfflineWriteTriageVerificationRejected("detached verification acquired authority")
    stable()
    return result
