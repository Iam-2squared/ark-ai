"""Read-only binding of synthetic Planner recovery to durable WRITE slots.

SQLite reservations are not external outcomes, consent, or execution rights.
An UNKNOWN/RUNNING WRITE remains quarantined even when the slot is present.
No ToolBackend, clock, network, notification, or OS effect is invoked.
"""

from __future__ import annotations

import hashlib
import json
import sqlite3
from contextlib import closing
from dataclasses import dataclass

from .disconnected_write_recovery_fence import (
    OfflineRecoveryFence,
    OfflineRecoveryStepClaim,
    review_disconnected_recovery_fence,
)
from .disconnected_write_slot_ledger import (
    DisconnectedWriteSlotLedger,
    WriteSlotLedgerWitness,
    _check_witness,
    _inspect,
)


class OfflineWriteRestartRejected(ValueError):
    """The detached WRITE restart claim cannot be safely reconciled."""


@dataclass(frozen=True, slots=True)
class OfflineWriteRestartReport:
    plan_id: str
    total_steps: int
    reserved_write_steps: int
    quarantined_write_steps: int
    fingerprint: str

    @property
    def tool_dispatch_authorized(self) -> bool:
        return False

    @property
    def write_replay_authorized(self) -> bool:
        return False

    @property
    def external_outcome_verified(self) -> bool:
        return False

    @property
    def trusted_clock_verified(self) -> bool:
        return False

    @property
    def consent_verified(self) -> bool:
        return False

    @property
    def cross_store_atomicity_proven(self) -> bool:
        return False


_LEDGER = DisconnectedWriteSlotLedger
_WITNESS = WriteSlotLedgerWitness
_STEP = OfflineRecoveryStepClaim
_FENCE = OfflineRecoveryFence
_REPORT = OfflineWriteRestartReport
_DOMAIN = b"ARK-disconnected-write-restart-binding-v1\0"


def review_disconnected_write_restart(
    ledger: DisconnectedWriteSlotLedger,
    retained: WriteSlotLedgerWitness,
    plan_id: str,
    steps: tuple[OfflineRecoveryStepClaim, ...],
) -> OfflineWriteRestartReport:
    """Require registered reservation membership without releasing any WRITE.

    The persisted ledger is inspected in a single read-only transaction, but
    the Planner claim is not in that transaction. A recheck reduces drift and
    does not turn caller-controlled status or a hash into trusted provenance.
    """
    if (
        type(ledger) is not _LEDGER
        or type(retained) is not _WITNESS
        or type(plan_id) is not str
        or type(steps) is not tuple
        or not 1 <= len(steps) <= 24
        or any(type(step) is not _STEP for step in steps)
    ):
        raise OfflineWriteRestartRejected("exact bounded WRITE restart inputs required")
    _check_witness(retained)
    path = ledger._path
    prior_count, prior_hash = retained.count, retained.chain_sha256
    originals = tuple(steps)
    saved = tuple((
        step.step_id, step.effect, step.depends_on,
        step.state, step.result_sha256, step.reservation_id,
    ) for step in originals)
    original_plan = plan_id
    original_steps = steps

    def stable() -> None:
        if (
            type(ledger) is not _LEDGER
            or ledger._path is not path
            or type(retained) is not _WITNESS
            or retained.count is not prior_count
            or retained.chain_sha256 is not prior_hash
            or retained.independently_authenticated is not False
            or plan_id is not original_plan
            or steps is not original_steps
            or len(steps) != len(originals)
        ):
            raise OfflineWriteRestartRejected("WRITE restart carriers changed")
        for current, original, fields in zip(steps, originals, saved, strict=True):
            if (
                type(current) is not _STEP
                or current is not original
                or any(now is not before for now, before in zip(
                    (current.step_id, current.effect, current.depends_on,
                     current.state, current.result_sha256, current.reservation_id),
                    fields, strict=True,
                ))
            ):
                raise OfflineWriteRestartRejected("WRITE restart step changed")

    stable()
    try:
        fence = review_disconnected_recovery_fence(plan_id, steps)
    except (TypeError, ValueError) as exc:
        raise OfflineWriteRestartRejected("Planner restart quarantine denied") from exc
    stable()
    if (
        type(fence) is not _FENCE
        or fence.plan_id is not original_plan
        or type(fence.decisions) is not tuple
        or len(fence.decisions) != len(steps)
        or type(fence.digest) is not str
        or len(fence.digest) != 64
    ):
        raise OfflineWriteRestartRejected("Planner quarantine result invalid")
    # Revalidate every disposition, including exact step membership and the
    # inert authority flags, before consulting durable reservations.
    if (
        fence.dispatch_authorized is not False
        or fence.automatic_replay_authorized is not False
        or fence.write_authorized is not False
        or fence.external_outcome_verified is not False
        or any(
            item.step_id != fields[0]
            for item, fields in zip(fence.decisions, saved, strict=True)
        )
    ):
        raise OfflineWriteRestartRejected("Planner quarantine receipt changed")
    fence_epoch = (fence, fence.decisions, fence.digest)
    disposition_epoch = tuple(
        (item, item.step_id, item.code) for item in fence.decisions
    )

    def assert_fence() -> None:
        if (
            type(fence) is not _FENCE
            or fence is not fence_epoch[0]
            or fence.decisions is not fence_epoch[1]
            or fence.digest is not fence_epoch[2]
            or fence.dispatch_authorized is not False
            or fence.automatic_replay_authorized is not False
            or fence.write_authorized is not False
            or fence.external_outcome_verified is not False
            or any(
                type(item) is not type(original)
                or item is not original
                or item.step_id is not name
                or item.code is not code
                for item, (original, name, code) in zip(
                    fence.decisions, disposition_epoch, strict=True,
                )
            )
        ):
            raise OfflineWriteRestartRejected("Planner quarantine changed")

    stable()
    assert_fence()
    try:
        with closing(ledger._open(read_only=True)) as conn:
            conn.execute("BEGIN")
            try:
                observed = _inspect(conn)
                stable()
                assert_fence()
                if observed != retained:
                    raise OfflineWriteRestartRejected("durable WRITE history differs")
                rows = tuple(conn.execute(
                    "SELECT plan_id,step_id,slot_id FROM synthetic_write_slots"
                ))
                reserved = frozenset(rows)
                matched = []
                for fields, decision in zip(saved, fence.decisions, strict=True):
                    step_id, effect, _, _, _, slot_id = fields
                    if effect == "WRITE" and slot_id is not None:
                        if (plan_id, step_id, slot_id) not in reserved:
                            raise OfflineWriteRestartRejected(
                                "claimed WRITE reservation is not bound to persisted slot"
                            )
                        matched.append((step_id, slot_id))
                    if effect == "WRITE" and decision.code == "READY_MOCK_ONLY":
                        raise OfflineWriteRestartRejected(
                            "WRITE was incorrectly released by quarantine"
                        )
                stable()
                assert_fence()
                if _inspect(conn) != observed:
                    raise OfflineWriteRestartRejected("WRITE ledger changed during review")
                conn.commit()
            except BaseException:
                conn.rollback()
                raise
    except sqlite3.Error as exc:
        raise OfflineWriteRestartRejected("WRITE ledger cannot be inspected") from exc
    stable()
    assert_fence()
    try:
        if ledger.inspect(retained=retained) != observed:
            raise OfflineWriteRestartRejected("WRITE ledger changed after read")
    except ValueError as exc:
        raise OfflineWriteRestartRejected("WRITE witness no longer matches") from exc
    stable()
    assert_fence()
    count = sum(
        fields[1] == "WRITE" and item.code.startswith("QUARANTINE_")
        for fields, item in zip(saved, fence.decisions, strict=True)
    )
    payload = json.dumps(
        (plan_id, fence.digest, (prior_count, prior_hash), matched, count),
        ensure_ascii=True, separators=(",", ":"),
    ).encode("ascii")
    digest = hashlib.sha256(_DOMAIN + payload).hexdigest()
    stable()
    assert_fence()
    report = OfflineWriteRestartReport(plan_id, len(steps), len(matched), count, digest)
    stable()
    assert_fence()
    if (
        type(report) is not _REPORT
        or report.plan_id is not plan_id
        or report.total_steps != len(steps)
        or report.reserved_write_steps != len(matched)
        or report.quarantined_write_steps != count
        or report.fingerprint is not digest
        or report.tool_dispatch_authorized is not False
        or report.write_replay_authorized is not False
        or report.external_outcome_verified is not False
        or report.trusted_clock_verified is not False
        or report.consent_verified is not False
        or report.cross_store_atomicity_proven is not False
    ):
        raise OfflineWriteRestartRejected("WRITE restart report acquired authority")
    return report
