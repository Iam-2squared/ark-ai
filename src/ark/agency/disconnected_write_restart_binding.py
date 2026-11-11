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
_ORIGINAL_REPORT_INIT = vars(_REPORT)["__init__"]
_REPORT_FIELDS = (
    "plan_id", "total_steps", "reserved_write_steps",
    "quarantined_write_steps", "fingerprint",
)
_REPORT_HOOKS = ("__new__", "__getattribute__", "__getattr__")
_ORIGINAL_REPORT_FIELDS = tuple(vars(_REPORT)[name] for name in _REPORT_FIELDS)
_ORIGINAL_REPORT_HOOKS = tuple(vars(_REPORT).get(name) for name in _REPORT_HOOKS)
# Unlike a late capture after SQLite review, import-original False-only
# descriptors cannot be silently replaced by an intervening ledger callback.
_REPORT_DENIAL_NAMES = (
    "tool_dispatch_authorized", "write_replay_authorized",
    "external_outcome_verified", "trusted_clock_verified",
    "consent_verified", "cross_store_atomicity_proven",
)
_ORIGINAL_REPORT_DENIALS = tuple(
    vars(_REPORT)[name] for name in _REPORT_DENIAL_NAMES
)
_DOMAIN = b"ARK-disconnected-write-restart-binding-v1\0"



# The retained WRITE diagnostic must not run a substituted serializer or hash
# while reviewing private fixture evidence. This is process-local definition
# custody only; it provides no independent provenance or trusted audit clock.
_ORIGINAL_JSON_DUMPS = json.dumps
_ORIGINAL_SHA256 = hashlib.sha256
_ORIGINAL_DOMAIN = _DOMAIN


def _assert_original_fingerprint_primitives() -> None:
    if (
        json.dumps is not _ORIGINAL_JSON_DUMPS
        or hashlib.sha256 is not _ORIGINAL_SHA256
        or _DOMAIN is not _ORIGINAL_DOMAIN
    ):
        raise OfflineWriteRestartRejected("WRITE restart digest implementation changed")

def _assert_original_report_constructor() -> None:
    # The inert report is constructed only after SQLite and Planner callbacks.
    # Check field descriptors and lookup hooks BEFORE opening the ledger: a
    # substituted slot can execute code during report construction/read even
    # if its initializer and false-only authority flags appear unchanged.
    if (
        OfflineWriteRestartReport is not _REPORT
        or vars(_REPORT).get("__init__") is not _ORIGINAL_REPORT_INIT
        or any(
            vars(_REPORT).get(name) is not original
            for name, original in zip(
                _REPORT_FIELDS, _ORIGINAL_REPORT_FIELDS, strict=True,
            )
        )
        or any(
            vars(_REPORT).get(name) is not original
            for name, original in zip(
                _REPORT_HOOKS, _ORIGINAL_REPORT_HOOKS, strict=True,
            )
        )
    ):
        raise OfflineWriteRestartRejected("WRITE restart report constructor changed")


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
    _assert_original_report_constructor()
    _assert_original_fingerprint_primitives()
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
        _assert_original_report_constructor()
        _assert_original_fingerprint_primitives()
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

    def matches_retained_tip(value: object) -> bool:
        # Dataclass equality can be rebound at runtime. A restart review
        # must validate each independently observed SQLite tip by scalars.
        if type(value) is not _WITNESS:
            return False
        try:
            _check_witness(value)
        except ValueError:
            return False
        return value.count == prior_count and value.chain_sha256 == prior_hash

    stable()
    assert_fence()
    try:
        with closing(ledger._open(read_only=True)) as conn:
            conn.execute("BEGIN")
            try:
                observed = _inspect(conn)
                stable()
                assert_fence()
                if not matches_retained_tip(observed):
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
                # Membership alone can omit an already-reserved WRITE from
                # the caller's plan. A partial restart claim must not be
                # presented as reconciliation of the complete persisted plan.
                # Reservations for *other* plans are independent and allowed.
                persisted_for_plan = frozenset(
                    (step_id, slot_id)
                    for saved_plan, step_id, slot_id in rows
                    if saved_plan == plan_id
                )
                if frozenset(matched) != persisted_for_plan:
                    raise OfflineWriteRestartRejected(
                        "unrepresented durable WRITE reservations for this plan"
                    )
                stable()
                assert_fence()
                if not matches_retained_tip(_inspect(conn)):
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
        if not matches_retained_tip(ledger.inspect(retained=retained)):
            raise OfflineWriteRestartRejected("WRITE ledger changed after read")
        # The public inspect method is an overridable callback. A callback
        # returning a stale, equal-valued result while appending a reservation
        # cannot rebase our earlier committed SQLite epoch. Reopen and read
        # the actual rows independently after that callback.
        stable()
        assert_fence()
        with closing(ledger._open(read_only=True)) as second:
            second.execute("BEGIN")
            try:
                if not matches_retained_tip(_inspect(second)):
                    raise OfflineWriteRestartRejected("WRITE ledger changed after read")
                second.commit()
            except BaseException:
                second.rollback()
                raise
    except sqlite3.Error as exc:
        raise OfflineWriteRestartRejected("WRITE ledger cannot be rechecked") from exc
    except ValueError as exc:
        if type(exc) is OfflineWriteRestartRejected:
            raise
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
    _assert_original_report_constructor()
    report = _REPORT(plan_id, len(steps), len(matched), count, digest)
    stable()
    assert_fence()
    # A false-valued authority getter is still a reentrant callback.
    # Capture the original result carriers before invoking any of them;
    # no getter may rewrite the report, original Planner claim or slot ledger.
    expected_report = (plan_id, len(steps), len(matched), count, digest)
    # False-valued authority getters can still rebind another descriptor,
    # including a descriptor that itself continues to return False.
    denials = (
        "tool_dispatch_authorized", "write_replay_authorized",
        "external_outcome_verified", "trusted_clock_verified",
        "consent_verified", "cross_store_atomicity_proven",
    )
    denial_descriptors = tuple(getattr(_REPORT, name) for name in denials)

    def stable_report() -> None:
        if (
            type(report) is not _REPORT
            or any(now is not prior for now, prior in zip((
                report.plan_id, report.total_steps,
                report.reserved_write_steps, report.quarantined_write_steps,
                report.fingerprint,
            ), expected_report, strict=True))
            or any(getattr(_REPORT, name) is not pinned
                   for name, pinned in zip(denials, denial_descriptors, strict=True))
        ):
            raise OfflineWriteRestartRejected("WRITE restart report changed after review")

    stable_report()
    for name in denials:
        if getattr(report, name) is not False:
            raise OfflineWriteRestartRejected("WRITE restart report acquired authority")
        stable_report()
        stable()
        assert_fence()

    # A False-valued final getter may also rewrite the durable WRITE ledger
    # while leaving the report and claimant carriers unchanged. Reopen an
    # independent read-only transaction after the LAST authority callback.
    try:
        with closing(ledger._open(read_only=True)) as final:
            final.execute("BEGIN")
            try:
                if not matches_retained_tip(_inspect(final)):
                    raise OfflineWriteRestartRejected(
                        "WRITE ledger changed after final authority denial"
                    )
                final.commit()
            except BaseException:
                final.rollback()
                raise
    except sqlite3.Error as exc:
        raise OfflineWriteRestartRejected(
            "WRITE ledger cannot be verified after denial"
        ) from exc
    # The final SQLite inspection is a callback boundary too: an injected
    # adapter can mutate a previously verified Planner claim or disposition
    # without changing the SQLite rows. Reject that post-read drift.
    stable()
    assert_fence()
    stable_report()
    # Old fault-injection contracts exercise denied getters and their
    # post-callback integrity checks. A pre-read check on the False-only
    # descriptor conflicts with those established fail-closed contracts:
    # validate original identity AFTER those final-denial callbacks instead.
    # The result is never dispatched or granted authority by this review.
    if any(
        vars(_REPORT).get(name) is not original
        for name, original in zip(
            _REPORT_DENIAL_NAMES, _ORIGINAL_REPORT_DENIALS, strict=True,
        )
    ):
        raise OfflineWriteRestartRejected(
            "WRITE restart denial descriptor changed after review"
        )
    return report
