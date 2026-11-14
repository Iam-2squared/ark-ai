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
    OfflineRecoveryDisposition,
    OfflineRecoveryFence,
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
_ORIGINAL_ITEM_INIT = vars(_ITEM_TYPE)["__init__"]
# Fail closed before any private recovery or SQLite evidence enters a replaced
# serializer/hash callback. These are process-local implementation identities,
# not authenticated custody or a sandbox.
_ORIGINAL_SHA256 = hashlib.sha256
_ORIGINAL_JSON_DUMPS = json.dumps
_ORIGINAL_DOMAIN = _DOMAIN
_PACKET_TYPE = OfflineWriteTriagePacket
_ORIGINAL_PACKET_INIT = vars(_PACKET_TYPE)["__init__"]
_RESTART_TYPE = OfflineWriteRestartReport
_FENCE_TYPE = OfflineRecoveryFence
_STEP_TYPE = OfflineRecoveryStepClaim
_PACKET_DENIALS = (
    "human_review_completed", "external_outcome_verified",
    "dispatch_authorized", "automatic_replay_authorized",
)
_RESTART_DENIALS = (
    "tool_dispatch_authorized", "write_replay_authorized",
    "external_outcome_verified", "trusted_clock_verified",
    "consent_verified", "cross_store_atomicity_proven",
)
_FENCE_DENIALS = (
    "dispatch_authorized", "automatic_replay_authorized",
    "write_authorized", "external_outcome_verified",
)
_ORIGINAL_DENIALS = tuple(
    (cls, names, tuple(vars(cls)[name] for name in names))
    for cls, names in (
        (_PACKET_TYPE, _PACKET_DENIALS),
        (_RESTART_TYPE, _RESTART_DENIALS),
        (_FENCE_TYPE, _FENCE_DENIALS),
    )
)


def _require_original_denial_descriptors() -> None:
    """Never invoke a replaced False-valued diagnostic authority getter."""
    if (
        OfflineWriteTriagePacket is not _PACKET_TYPE
        or hashlib.sha256 is not _ORIGINAL_SHA256
        or json.dumps is not _ORIGINAL_JSON_DUMPS
        or _DOMAIN is not _ORIGINAL_DOMAIN
        or OfflineWriteTriageItem is not _ITEM_TYPE
        or vars(_PACKET_TYPE).get("__init__") is not _ORIGINAL_PACKET_INIT
        or vars(_ITEM_TYPE).get("__init__") is not _ORIGINAL_ITEM_INIT
        or OfflineWriteRestartReport is not _RESTART_TYPE
        or OfflineRecoveryFence is not _FENCE_TYPE
        or any(
            vars(cls).get(name) is not descriptor
            for cls, names, descriptors in _ORIGINAL_DENIALS
            for name, descriptor in zip(names, descriptors, strict=True)
        )
    ):
        raise OfflineWriteTriageRejected(
            "manual WRITE triage authority descriptor changed"
        )


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
    _require_original_denial_descriptors()
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
        _require_original_denial_descriptors()
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
        or type(fence) is not OfflineRecoveryFence
        or fence.plan_id != plan_id
        or type(fence.decisions) is not tuple
        or len(fence.decisions) != len(steps)
        or type(fence.digest) is not str
        or _SHA.fullmatch(fence.digest) is None
        or any(type(item) is not OfflineRecoveryDisposition
               for item in fence.decisions)
    ):
        raise OfflineWriteTriageRejected("local recovery proof gained authority")

    # The child is a Python callback result, not independent custody.
    # Verify its complete canonical digest and exact carrier types here,
    # not merely the claimed per-step disposition string.
    fence_epoch = tuple(
        (item, item.step_id, item.code) for item in fence.decisions
    )
    fence_pin = (fence.plan_id, fence.decisions, fence.digest)

    def stable_fence() -> None:
        if (
            type(fence) is not OfflineRecoveryFence
            or fence.plan_id is not fence_pin[0]
            or fence.decisions is not fence_pin[1]
            or fence.digest is not fence_pin[2]
            or len(fence.decisions) != len(fence_epoch)
            or any(
                type(item) is not OfflineRecoveryDisposition
                or item is not saved_item
                or item.step_id is not step_id or item.code is not code
                for item, (saved_item, step_id, code) in zip(
                    fence.decisions, fence_epoch, strict=True,
                )
            )
        ):
            raise OfflineWriteTriageRejected("manual WRITE disposition changed")
        stable()

    stable_fence()
    if any(
        type(item.step_id) is not str or type(item.code) is not str
        for item in fence.decisions
    ):
        raise OfflineWriteTriageRejected("noncanonical manual WRITE disposition")
    canonical = tuple(
        (*fields, item.code)
        for fields, item in zip(saved, fence.decisions, strict=True)
    )
    raw = json.dumps(
        (plan_id, canonical), ensure_ascii=True, separators=(",", ":"),
    ).encode("ascii")
    expected_fence_digest = hashlib.sha256(
        b"ARK-disconnected-mixed-recovery-fence-v1\0" + raw
    ).hexdigest()
    if fence.digest != expected_fence_digest:
        raise OfflineWriteTriageRejected("manual WRITE fence digest mismatch")
    stable_fence()
    for name in (
        "dispatch_authorized", "automatic_replay_authorized",
        "write_authorized", "external_outcome_verified",
    ):
        if getattr(fence, name) is not False:
            raise OfflineWriteTriageRejected("manual WRITE fence gained authority")
        stable_fence()
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
        # Item initialization can run caller-modified code. Reconfirm the
        # original constructor immediately before executing it, not only
        # after constructing the complete operator packet.
        _require_original_denial_descriptors()
        packet_items.append(_ITEM_TYPE(
            step_id, state, decision.code, reservation, investigation,
        ))
        stable()
        stable_fence()
    if recovery.reserved_write_steps != sum(
        item.reservation_id is not None for item in packet_items
    ):
        raise OfflineWriteTriageRejected("durable reservation coverage changed")
    pinned = tuple(packet_items)
    item_epoch = tuple((
        item, item.step_id, item.claimed_state, item.disposition,
        item.reservation_id, item.investigation,
    ) for item in pinned)
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
    # Packet construction itself is a callback boundary in synthetic faults.
    _require_original_denial_descriptors()
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
    # A false-valued denial property is still a Python callback. It can
    # reflectively edit a frozen packet or a nested item after the digest was
    # calculated. Check *all* retained fields after the final denial getter.
    def assert_packet_epoch() -> None:
        if (
            type(packet) is not _PACKET_TYPE
            or packet.plan_id is not plan_id
            or packet.items is not pinned
            or packet.reservation_chain_sha256 is not previous_chain
            or packet.recovery_fingerprint is not recovery.fingerprint
            or packet.packet_sha256 is not fingerprint
            or len(packet.items) != len(item_epoch)
            or any(
                type(item) is not _ITEM_TYPE
                or item is not saved[0]
                or any(now is not old for now, old in zip((
                    item.step_id, item.claimed_state, item.disposition,
                    item.reservation_id, item.investigation,
                ), saved[1:], strict=True))
                for item, saved in zip(packet.items, item_epoch, strict=True)
            )
        ):
            raise OfflineWriteTriageRejected(
                "operator packet or nested item changed after authority denial"
            )

    stable()
    assert_packet_epoch()
    if (
        packet.human_review_completed is not False
        or packet.external_outcome_verified is not False
        or packet.dispatch_authorized is not False
        or packet.automatic_replay_authorized is not False
    ):
        raise OfflineWriteTriageRejected("operator packet acquired authority")
    stable()
    stable_fence()
    assert_packet_epoch()
    return packet
