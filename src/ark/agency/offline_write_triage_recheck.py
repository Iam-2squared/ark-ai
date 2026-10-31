"""Reconcile a detached WRITE checklist with retained claims and a live local ledger.

This is a read-only, disconnected *investigation* check. Caller-provided
recovery claims and retained witness are not independently authenticated; a
matching result is NEVER approval, observed external effect, or retry permission.
"""

from __future__ import annotations

from dataclasses import dataclass

from .disconnected_write_recovery_fence import OfflineRecoveryStepClaim
from .disconnected_write_slot_ledger import (
    DisconnectedWriteSlotLedger,
    WriteSlotLedgerRejected,
    WriteSlotLedgerWitness,
)
from .offline_write_manual_triage import (
    OfflineWriteTriagePacket,
    OfflineWriteTriageRejected,
    build_offline_write_triage_packet,
)
from .offline_write_triage_verify import (
    OfflineWriteTriageVerificationRejected,
    verify_offline_write_triage_packet,
)


class OfflineWriteTriageRecheckRejected(ValueError):
    """Packet, claims, or read-only reservation ledger cannot be reconciled."""


@dataclass(frozen=True, slots=True)
class OfflineWriteTriageRecheck:
    plan_id: str
    packet_sha256: str
    retained_count: int
    write_count: int
    uncertain_write_count: int

    @property
    def independent_human_review_proven(self) -> bool:
        return False

    @property
    def external_effect_proven(self) -> bool:
        return False

    @property
    def dispatch_authorized(self) -> bool:
        return False

    @property
    def replay_authorized(self) -> bool:
        return False


_RESULT = OfflineWriteTriageRecheck


def recheck_offline_write_triage(
    ledger: DisconnectedWriteSlotLedger,
    retained: WriteSlotLedgerWitness,
    plan_id: str,
    steps: tuple[OfflineRecoveryStepClaim, ...],
    packet: OfflineWriteTriagePacket,
) -> OfflineWriteTriageRecheck:
    """Rebuild a checksum-bound manual checklist from the original local claims.

    Unlike a detached checksum alone, this checks the current on-disk
    reservation chain and the supplied claimed step states. It intentionally
    does not resolve UNKNOWN/RUNNING effects or grant external authority.
    """
    if (
        type(ledger) is not DisconnectedWriteSlotLedger
        or type(retained) is not WriteSlotLedgerWitness
        or type(plan_id) is not str
        or type(steps) is not tuple or not 1 <= len(steps) <= 24
        or type(packet) is not OfflineWriteTriagePacket
        or any(type(s) is not OfflineRecoveryStepClaim for s in steps)
    ):
        raise OfflineWriteTriageRecheckRejected("exact local triage inputs required")

    path = ledger._path
    witness_epoch = (retained.count, retained.chain_sha256)
    packet_epoch = (
        packet.plan_id, packet.items, packet.reservation_chain_sha256,
        packet.recovery_fingerprint, packet.packet_sha256,
    )
    step_epoch = tuple((
        step, step.step_id, step.effect, step.depends_on, step.state,
        step.result_sha256, step.reservation_id,
    ) for step in steps)

    def stable() -> None:
        if (
            type(ledger) is not DisconnectedWriteSlotLedger
            or ledger._path is not path
            or type(retained) is not WriteSlotLedgerWitness
            or retained.count is not witness_epoch[0]
            or retained.chain_sha256 is not witness_epoch[1]
            or type(packet) is not OfflineWriteTriagePacket
            or any(now is not old for now, old in zip(
                (
                    packet.plan_id, packet.items, packet.reservation_chain_sha256,
                    packet.recovery_fingerprint, packet.packet_sha256,
                ),
                packet_epoch, strict=True,
            ))
            or len(steps) != len(step_epoch)
        ):
            raise OfflineWriteTriageRecheckRejected("triage inputs changed during recheck")
        for step, saved in zip(steps, step_epoch, strict=True):
            if (
                type(step) is not OfflineRecoveryStepClaim or step is not saved[0]
                or any(now is not old for now, old in zip(
                    (
                        step.step_id, step.effect, step.depends_on, step.state,
                        step.result_sha256, step.reservation_id,
                    ),
                    saved[1:], strict=True,
                ))
            ):
                raise OfflineWriteTriageRecheckRejected("triage step epoch changed")

    stable()
    try:
        verified = verify_offline_write_triage_packet(packet, retained)
        stable()
        # Rebuild via the existing restart/fence reviewers. This inspects
        # the persistent reservation ledger read-only rather than trusting a
        # detached packet and retained digest in isolation.
        rebuilt = build_offline_write_triage_packet(ledger, retained, plan_id, steps)
        stable()
        again = verify_offline_write_triage_packet(packet, retained)
        stable()
    except (
        OfflineWriteTriageVerificationRejected,
        OfflineWriteTriageRejected,
        WriteSlotLedgerRejected,
        TypeError,
        AttributeError,
    ) as exc:
        raise OfflineWriteTriageRecheckRejected("live local WRITE recheck denied") from exc

    if (
        type(verified) is not type(again)
        or verified != again
        or rebuilt != packet
        or type(rebuilt) is not OfflineWriteTriagePacket
        or rebuilt.plan_id != plan_id
        or verified.packet_sha256 != packet_epoch[4]
        or verified.retained_count != witness_epoch[0]
        or verified.dispatch_authorized is not False
        or verified.automatic_replay_authorized is not False
        or verified.external_outcome_verified is not False
        or rebuilt.dispatch_authorized is not False
        or rebuilt.automatic_replay_authorized is not False
        or rebuilt.external_outcome_verified is not False
        or rebuilt.human_review_completed is not False
    ):
        raise OfflineWriteTriageRecheckRejected("manual WRITE evidence mismatch or authority")
    stable()
    count = len(rebuilt.items)
    uncertain = sum(
        item.claimed_state in {"UNKNOWN", "RUNNING"} for item in rebuilt.items
    )
    result = _RESULT(plan_id, packet_epoch[4], witness_epoch[0], count, uncertain)
    if (
        type(result) is not _RESULT
        or result.plan_id is not plan_id
        or result.packet_sha256 is not packet_epoch[4]
        or result.retained_count is not witness_epoch[0]
        or type(result.write_count) is not int or result.write_count != count
        or type(result.uncertain_write_count) is not int
        or result.uncertain_write_count != uncertain
        or result.independent_human_review_proven is not False
        or result.external_effect_proven is not False
        or result.dispatch_authorized is not False
        or result.replay_authorized is not False
    ):
        raise OfflineWriteTriageRecheckRejected("WRITE recheck result acquired authority")
    stable()
    return result
