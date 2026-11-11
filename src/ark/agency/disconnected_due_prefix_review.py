"""One-transaction retained-prefix audit of synthetic due-slot reservations.

An appended ledger tail cannot excuse rewriting an earlier reservation. The
retained witness MUST be independently held by the caller, but its custody is
not authenticated here. This is read-only review of disconnected fixtures,
not a scheduler, consent, notification, trusted clock, or Tool authority.
"""

from __future__ import annotations

import hashlib
import json
import sqlite3
from contextlib import closing
from dataclasses import dataclass

from . import disconnected_due_reservation as due


class DisconnectedDuePrefixRejected(ValueError):
    """A retained synthetic due reservation prefix cannot be reconciled."""


@dataclass(frozen=True, slots=True)
class DisconnectedDuePrefixReview:
    previous_count: int
    current_count: int
    current_fingerprint: str
    status: str
    review_sha256: str

    @property
    def independently_authenticated(self) -> bool:
        return False

    @property
    def historical_writer_proven(self) -> bool:
        return False

    @property
    def trusted_clock_verified(self) -> bool:
        return False

    @property
    def notification_authorized(self) -> bool:
        return False

    @property
    def tool_dispatch_authorized(self) -> bool:
        return False

    @property
    def automatic_replay_authorized(self) -> bool:
        return False


_DOMAIN = b"ARK-disconnected-due-retained-prefix-v1\0"
_RESULT = DisconnectedDuePrefixReview
_ORIGINAL_RESULT_INIT = vars(_RESULT)["__init__"]
_WITNESS = due.DueReservationWitness
_LEDGER = due.DisconnectedDueReservations
# An alternate witness validator/digest could accept or forge a historical
# prefix before SQLite's retained rows are compared. Keep original local
# callbacks and the outer reconciliation digest fixed at import time.
# This is interpreter-local custody, NOT authenticated provenance.
_ORIGINAL_WITNESS_CHECK = due._check_witness
_ORIGINAL_DUE_DIGEST = due._digest
_ORIGINAL_SHA256 = hashlib.sha256
_ORIGINAL_DUMPS = json.dumps
_ORIGINAL_DOMAIN = _DOMAIN

# Original descriptors, not just False-valued callbacks, are part of the
# passive review boundary. A substituted property can return False while
# changing the SQLite source, retained witness, or displayed result.
_DENIAL_FLAGS = (
    "independently_authenticated", "historical_writer_proven",
    "trusted_clock_verified", "notification_authorized",
    "tool_dispatch_authorized", "automatic_replay_authorized",
)
_ORIGINAL_DENIALS = tuple(vars(_RESULT)[flag] for flag in _DENIAL_FLAGS)
_ORIGINAL_WITNESS_DENIAL = _WITNESS.independent_custody_proven

# A frozen slotted result/witness remains executable when its field
# descriptors or lookup hooks are replaced. Static class-dictionary checks
# must run before reading retained private slot values, opening SQLite, or
# constructing a result; false-valued properties alone are insufficient.
_RESULT_FIELDS = (
    "previous_count", "current_count", "current_fingerprint",
    "status", "review_sha256",
)
_WITNESS_FIELDS = ("count", "fingerprint")
_CARRIER_HOOKS = ("__init__", "__new__", "__getattribute__", "__getattr__")
_ORIGINAL_RESULT_FIELDS = tuple(vars(_RESULT)[name] for name in _RESULT_FIELDS)
_ORIGINAL_WITNESS_FIELDS = tuple(vars(_WITNESS)[name] for name in _WITNESS_FIELDS)
_ORIGINAL_RESULT_HOOKS = tuple(
    vars(_RESULT).get(name) for name in _CARRIER_HOOKS
)
_ORIGINAL_WITNESS_HOOKS = tuple(
    vars(_WITNESS).get(name) for name in _CARRIER_HOOKS
)


def _require_original_denials() -> None:
    if (
        due.DueReservationWitness is not _WITNESS
        or due._check_witness is not _ORIGINAL_WITNESS_CHECK
        or due._digest is not _ORIGINAL_DUE_DIGEST
        or hashlib.sha256 is not _ORIGINAL_SHA256
        or json.dumps is not _ORIGINAL_DUMPS
        or _DOMAIN is not _ORIGINAL_DOMAIN
        or due.DisconnectedDueReservations is not _LEDGER
        or any(
            vars(cls).get(name) is not original
            for cls, names, originals in (
                (_RESULT, _RESULT_FIELDS, _ORIGINAL_RESULT_FIELDS),
                (_WITNESS, _WITNESS_FIELDS, _ORIGINAL_WITNESS_FIELDS),
                (_RESULT, _CARRIER_HOOKS, _ORIGINAL_RESULT_HOOKS),
                (_WITNESS, _CARRIER_HOOKS, _ORIGINAL_WITNESS_HOOKS),
            )
            for name, original in zip(names, originals, strict=True)
        )
        or DisconnectedDuePrefixReview is not _RESULT
        or vars(_RESULT).get("__init__") is not _ORIGINAL_RESULT_INIT
        or any(
            vars(_RESULT).get(flag) is not original
            for flag, original in zip(_DENIAL_FLAGS, _ORIGINAL_DENIALS, strict=True)
        )
        or vars(_WITNESS).get("independent_custody_proven") is not _ORIGINAL_WITNESS_DENIAL
    ):
        raise DisconnectedDuePrefixRejected(
            "due prefix authority definition changed; source/witness untrusted"
        )


def review_retained_due_prefix(
    ledger: due.DisconnectedDueReservations,
    retained: due.DueReservationWitness,
) -> DisconnectedDuePrefixReview:
    """Recompute the older whole-row prefix while auditing one SQLite snapshot.

    A row update can restore a locally valid current hash and lifecycle
    without restoring the old prefix. Comparing only the new head and count
    cannot distinguish that alteration from a legitimate append.
    """
    if type(ledger) is not _LEDGER:
        raise DisconnectedDuePrefixRejected("exact local due ledger required")
    _require_original_denials()
    try:
        due._check_witness(retained)
    except due.DueReservationRejected as exc:
        raise DisconnectedDuePrefixRejected("invalid retained due witness") from exc
    old_count, old_fingerprint = retained.count, retained.fingerprint
    source_path = ledger._path

    def stable() -> None:
        _require_original_denials()
        if (
            type(ledger) is not _LEDGER
            or ledger._path is not source_path
            or type(retained) is not _WITNESS
            or retained.count is not old_count
            or retained.fingerprint is not old_fingerprint
            or retained.independent_custody_proven is not False
        ):
            raise DisconnectedDuePrefixRejected("due source/witness changed during review")

    stable()
    try:
        with closing(ledger._open(read_only=True)) as conn:
            stable()
            conn.execute("BEGIN")
            try:
                # This schema/lifecycle check and the historical prefix SELECT
                # must run in the SAME read transaction, not separate calls.
                current, _ = due._inspect(conn)
                stable()
                if (
                    type(current) is not _WITNESS
                    or current.independent_custody_proven is not False
                    or current.count < old_count
                ):
                    raise DisconnectedDuePrefixRejected(
                        "retained due reservation history rolled back"
                    )
                prior_rows = tuple(conn.execute(
                    "SELECT seq,occurrence_id,policy_sha256,due_at_ms,reserved_at_ms "
                    "FROM due_reservations WHERE seq<=? ORDER BY seq",
                    (old_count,),
                ))
                stable()
                if (
                    len(prior_rows) != old_count
                    or due._digest(prior_rows) != old_fingerprint
                ):
                    raise DisconnectedDuePrefixRejected(
                        "retained due reservation prefix changed"
                    )
                current_epoch = (current.count, current.fingerprint)
                stable()
                conn.rollback()
            except BaseException:
                conn.rollback()
                raise
    except (sqlite3.Error, due.DueReservationRejected) as exc:
        raise DisconnectedDuePrefixRejected(
            "local due reservation prefix unavailable"
        ) from exc

    stable()
    if current.count is not current_epoch[0] or current.fingerprint is not current_epoch[1]:
        raise DisconnectedDuePrefixRejected("observed due witness changed")
    status = (
        "ADVANCED_PREFIX_UNAUTHENTICATED"
        if current.count > old_count else "UNCHANGED_LOCAL_HISTORY"
    )
    encoded = json.dumps(
        (old_count, old_fingerprint, current_epoch, status),
        ensure_ascii=True, separators=(",", ":"),
    ).encode("ascii")
    stable()
    digest = hashlib.sha256(_DOMAIN + encoded).hexdigest()
    stable()
    result = _RESULT(old_count, current.count, current.fingerprint, status, digest)
    if (
        type(result) is not _RESULT
        or type(result.previous_count) is not int
        or result.previous_count != old_count
        or type(result.current_count) is not int
        or result.current_count != current_epoch[0]
        or result.current_fingerprint is not current_epoch[1]
        or result.status is not status
        or result.review_sha256 is not digest
        or result.independently_authenticated is not False
        or result.historical_writer_proven is not False
        or result.trusted_clock_verified is not False
        or result.notification_authorized is not False
        or result.tool_dispatch_authorized is not False
        or result.automatic_replay_authorized is not False
    ):
        raise DisconnectedDuePrefixRejected("due prefix review acquired authority")
    # A false-valued authority getter may reflectively mutate *any* field
    # of the frozen report, including status/count (not only its digest).
    # Check the complete result again AFTER the last denial callback and
    # after the final source/witness validation. This is still diagnostic;
    # it cannot certify a historic writer, clock, consent or notification.
    pinned_result = (old_count, current_epoch[0], current_epoch[1], status, digest)

    def stable_result() -> None:
        _require_original_denials()
        attributes = (
            "previous_count", "current_count", "current_fingerprint",
            "status", "review_sha256",
        )
        flags = (
            "independently_authenticated", "historical_writer_proven",
            "trusted_clock_verified", "notification_authorized",
            "tool_dispatch_authorized", "automatic_replay_authorized",
        )
        before = tuple(getattr(result, name) for name in attributes)
        if (
            type(result) is not _RESULT
            or type(before[0]) is not int
            or type(before[1]) is not int
            or any(type(value) is not str for value in before[2:])
            or any(a is not b for a, b in zip(before, pinned_result, strict=True))
            or any(getattr(result, flag) is not False for flag in flags)
        ):
            raise DisconnectedDuePrefixRejected(
                "due prefix review changed after denial"
            )
        # The *last* denial getter can itself mutate count/status or the
        # retained source. Do not return solely on pre-callback values.
        after = tuple(getattr(result, name) for name in attributes)
        if any(a is not b for a, b in zip(after, pinned_result, strict=True)):
            raise DisconnectedDuePrefixRejected(
                "due prefix review changed after final authority getter"
            )

    stable_result()
    stable()
    stable_result()
    stable()
    if (
        type(result) is not _RESULT
        or any(a is not b for a, b in zip(
            (
                result.previous_count, result.current_count,
                result.current_fingerprint, result.status, result.review_sha256,
            ),
            pinned_result, strict=True,
        ))
    ):
        raise DisconnectedDuePrefixRejected("due prefix result changed at return")
    return result
