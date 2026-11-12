"""Read-only uncertain schedule quarantine reconciliation after restart.

Only local, caller-controlled policy and SQLite prefix facts are compared.
No scheduler, clock attestation, user consent, notification or replay authority
is obtained even when the requested quarantine row is found.
"""

from __future__ import annotations

import sqlite3
from contextlib import closing
from dataclasses import dataclass

from . import disconnected_schedule_quarantine_ledger as module

QuarantinePolicy = module.QuarantinePolicy
QuarantineWitness = module.QuarantineWitness
DisconnectedScheduleQuarantineLedger = module.DisconnectedScheduleQuarantineLedger
_ORIGINAL_VALIDATE = module._validate
_ORIGINAL_POLICY = module._policy_epoch
_ORIGINAL_DERIVE = module.derive_quarantined_occurrence
_ORIGINAL_GENESIS = module.genesis_quarantine_witness
_ORIGINAL_CARRIERS = module._require_original_quarantine_input_carriers
_ORIGINAL_OPEN = vars(DisconnectedScheduleQuarantineLedger)["_open"]
_ORIGINAL_WITNESS = vars(DisconnectedScheduleQuarantineLedger)["_check_witness"]
_STATES = ("UNCHANGED", "LOCALLY_QUARANTINED", "PREEXISTING", "ADVANCED_OTHER")


class ScheduleUnknownQuarantineRejected(ValueError):
    """A synthetic quarantine outcome is too ambiguous to reconcile."""


@dataclass(frozen=True, slots=True)
class ScheduleUnknownQuarantineReview:
    occurrence_id: str
    local_state: str
    before_count: int
    observed_count: int
    locally_present: bool

    @property
    def notification_authorized(self) -> bool:
        return False

    @property
    def execution_authorized(self) -> bool:
        return False

    @property
    def automatic_replay_authorized(self) -> bool:
        return False

    @property
    def trusted_clock_verified(self) -> bool:
        return False

    @property
    def consent_verified(self) -> bool:
        return False

    @property
    def manual_review_required(self) -> bool:
        return True


_RESULT = ScheduleUnknownQuarantineReview
_RESULT_FIELDS = (
    "occurrence_id", "local_state", "before_count", "observed_count",
    "locally_present", "notification_authorized", "execution_authorized",
    "automatic_replay_authorized", "trusted_clock_verified", "consent_verified",
    "manual_review_required", "__init__", "__new__", "__getattribute__",
    "__getattr__",
)
_ORIGINAL_RESULT = tuple(vars(_RESULT).get(name) for name in _RESULT_FIELDS)


def _protocol() -> None:
    if (
        module._validate is not _ORIGINAL_VALIDATE
        or module._policy_epoch is not _ORIGINAL_POLICY
        or module.derive_quarantined_occurrence is not _ORIGINAL_DERIVE
        or module.genesis_quarantine_witness is not _ORIGINAL_GENESIS
        or module._require_original_quarantine_input_carriers is not _ORIGINAL_CARRIERS
        or vars(DisconnectedScheduleQuarantineLedger).get("_open") is not _ORIGINAL_OPEN
        or vars(DisconnectedScheduleQuarantineLedger).get("_check_witness")
        is not _ORIGINAL_WITNESS
        or module.QuarantinePolicy is not QuarantinePolicy
        or module.QuarantineWitness is not QuarantineWitness
        or module.DisconnectedScheduleQuarantineLedger is not DisconnectedScheduleQuarantineLedger
        or ScheduleUnknownQuarantineReview is not _RESULT
        or any(
            vars(_RESULT).get(name) is not original
            for name, original in zip(_RESULT_FIELDS, _ORIGINAL_RESULT, strict=True)
        )
    ):
        raise ScheduleUnknownQuarantineRejected("quarantine triage protocol changed")
    _ORIGINAL_CARRIERS()


def review_schedule_unknown_quarantine(
    ledger: DisconnectedScheduleQuarantineLedger,
    policy: QuarantinePolicy,
    before: QuarantineWitness,
    *,
    index: int,
    occurrence_id: str,
    observed_ms: int,
) -> ScheduleUnknownQuarantineReview:
    """Compare an uncertain quarantine row in a single read-only WAL epoch."""
    _protocol()
    if (
        type(ledger) is not DisconnectedScheduleQuarantineLedger
        or type(policy) is not QuarantinePolicy
        or type(before) is not QuarantineWitness
        or type(index) is not int
        or type(observed_ms) is not int
        or type(occurrence_id) is not str
    ):
        raise ScheduleUnknownQuarantineRejected("exact schedule triage inputs required")
    try:
        epoch = _ORIGINAL_POLICY(policy)
        _ORIGINAL_WITNESS(before)
        old = (before.count, before.chain_sha256)
        if (
            ledger._epoch != epoch
            or not 0 <= index < epoch[3]
            or not 0 <= observed_ms <= module._MAX_MS
            or observed_ms <= epoch[1] + index * epoch[2] + epoch[4]
            or occurrence_id != _ORIGINAL_DERIVE(policy, index)
        ):
            raise ScheduleUnknownQuarantineRejected("claim is not an expired policy slot")
        if old[0] == 0:
            genesis = _ORIGINAL_GENESIS(policy)
            if old != (genesis.count, genesis.chain_sha256):
                raise ScheduleUnknownQuarantineRejected("retained genesis mismatch")

        original_path = ledger._path
        original_epoch = ledger._epoch

        def stable() -> None:
            _protocol()
            _ORIGINAL_WITNESS(before)
            if (
                (before.count, before.chain_sha256) != old
                or _ORIGINAL_POLICY(policy) != epoch
                or ledger._path is not original_path
                or ledger._epoch is not original_epoch
            ):
                raise ScheduleUnknownQuarantineRejected("quarantine triage epoch changed")

        stable()
        with closing(ledger._open(read_only=True)) as conn:
            conn.execute("BEGIN")
            stable()
            current = _ORIGINAL_VALIDATE(conn, epoch)
            stable()
            count = current.count
            if count < old[0]:
                raise ScheduleUnknownQuarantineRejected("retained prefix ahead of ledger")
            if old[0]:
                prefix = conn.execute(
                    "SELECT chain_sha256 FROM quarantines WHERE seq=?", (old[0],),
                ).fetchone()
                if prefix != (old[1],):
                    raise ScheduleUnknownQuarantineRejected("retained prefix changed")
            rows = conn.execute(
                "SELECT seq,due_ms,observed_ms FROM quarantines "
                "WHERE occurrence_id=?", (occurrence_id,),
            ).fetchall()
            stable()
            if len(rows) > 1 or bool(rows) != (index < count):
                raise ScheduleUnknownQuarantineRejected("schedule occurrence membership changed")
            if rows and (
                rows[0][0] != index + 1
                or rows[0][1] != epoch[1] + index * epoch[2]
                or rows[0][2] != observed_ms
            ):
                raise ScheduleUnknownQuarantineRejected("quarantine occurrence evidence differs")
            if rows:
                state = "PREEXISTING" if index < old[0] else "LOCALLY_QUARANTINED"
            elif count == old[0]:
                state = "UNCHANGED"
            else:
                state = "ADVANCED_OTHER"
            if state not in _STATES or (
                count == old[0] and current.chain_sha256 != old[1]
            ):
                raise ScheduleUnknownQuarantineRejected("impossible quarantine state")
            stable()
        result = _RESULT(occurrence_id, state, old[0], count, bool(rows))
        _protocol()
        if (
            type(result) is not _RESULT
            or result.local_state not in _STATES
            or result.before_count != old[0]
            or result.observed_count != count
            or result.locally_present is not bool(rows)
            or result.notification_authorized is not False
            or result.execution_authorized is not False
            or result.automatic_replay_authorized is not False
            or result.trusted_clock_verified is not False
            or result.consent_verified is not False
            or result.manual_review_required is not True
        ):
            raise ScheduleUnknownQuarantineRejected("quarantine review acquired authority")
        stable()
        return result
    except (module.ScheduleQuarantineRejected, sqlite3.Error) as exc:
        raise ScheduleUnknownQuarantineRejected(
            "local quarantine evidence unavailable; manual review required"
        ) from exc
