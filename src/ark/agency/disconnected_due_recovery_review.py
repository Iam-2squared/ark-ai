"""Read-only retained due-slot restart triage for disconnected scheduler data.

The caller must retain the witness independently. An appended SQLite history
is *not* proof of historical prefix integrity, user consent, trusted time or
exactly-once real effects. No scheduling, notification or Tool is executed.
"""

from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass

from .disconnected_due_reservation import (
    DisconnectedDueReservations,
    DueReservationWitness,
)

_SHA = re.compile(r"[0-9a-f]{64}\Z")
_MAX_ROWS = 512
_DOMAIN = b"ARK-due-restart-triage-v1\0"
_LEDGER_TYPE = DisconnectedDueReservations
_WITNESS_TYPE = DueReservationWitness


class DisconnectedDueRecoveryRejected(ValueError):
    """A retained synthetic due witness regressed or cannot be trusted."""


@dataclass(frozen=True, slots=True)
class DisconnectedDueRecoveryReview:
    previous_count: int
    observed_count: int
    status: str
    digest: str

    @property
    def historical_prefix_proven(self) -> bool:
        return False

    @property
    def independently_custodied(self) -> bool:
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


_RESULT_TYPE = DisconnectedDueRecoveryReview


def _checked(value: object) -> tuple[int, str]:
    if (
        type(value) is not _WITNESS_TYPE
        or type(value.count) is not int
        or not 0 <= value.count <= _MAX_ROWS
        or type(value.fingerprint) is not str
        or _SHA.fullmatch(value.fingerprint) is None
        or value.independent_custody_proven is not False
    ):
        raise DisconnectedDueRecoveryRejected("invalid exact due witness")
    return (value.count, value.fingerprint)


def review_restarted_due_reservations(
    ledger: DisconnectedDueReservations,
    retained: DueReservationWitness,
) -> DisconnectedDueRecoveryReview:
    """Read one initialized local ledger and compare with a retained claim.

    Same-count rewrites and count regression are refused. Increased history
    is flagged UNVERIFIED rather than silently treated as a safe replay.
    """
    if type(ledger) is not _LEDGER_TYPE:
        raise DisconnectedDueRecoveryRejected("exact disconnected due ledger required")
    prior = _checked(retained)
    original_path = ledger._path

    def retained_epoch() -> None:
        if (
            type(ledger) is not _LEDGER_TYPE
            or ledger._path is not original_path
            or _checked(retained) != prior
            or retained.count is not prior[0]
            or retained.fingerprint is not prior[1]
        ):
            raise DisconnectedDueRecoveryRejected("retained due custody changed")

    retained_epoch()
    observed = ledger.witness()
    retained_epoch()
    current = _checked(observed)
    observed_count, observed_fingerprint = observed.count, observed.fingerprint

    def observed_epoch() -> None:
        retained_epoch()
        if (
            type(observed) is not _WITNESS_TYPE
            or _checked(observed) != current
            or observed.count is not observed_count
            or observed.fingerprint is not observed_fingerprint
        ):
            raise DisconnectedDueRecoveryRejected("observed due witness changed")

    observed_epoch()
    if current[0] < prior[0]:
        raise DisconnectedDueRecoveryRejected("retained due reservation count regressed")
    if current[0] == prior[0] and current[1] != prior[1]:
        raise DisconnectedDueRecoveryRejected("retained due history rewritten at same count")
    status = (
        "ADVANCED_HISTORY_UNVERIFIED"
        if current[0] > prior[0] else "UNCHANGED_LOCAL_HISTORY"
    )
    payload = json.dumps(
        (prior, current, status), separators=(",", ":"), ensure_ascii=True,
    ).encode("ascii")
    observed_epoch()
    digest = hashlib.sha256(_DOMAIN + payload).hexdigest()
    observed_epoch()
    result = DisconnectedDueRecoveryReview(prior[0], current[0], status, digest)
    observed_epoch()
    if (
        type(result) is not _RESULT_TYPE
        or result.previous_count is not prior[0]
        or result.observed_count is not current[0]
        or result.status is not status
        or result.digest is not digest
        or result.historical_prefix_proven is not False
        or result.independently_custodied is not False
        or result.trusted_clock_verified is not False
        or result.notification_authorized is not False
        or result.tool_dispatch_authorized is not False
        or result.automatic_replay_authorized is not False
    ):
        raise DisconnectedDueRecoveryRejected("due recovery result changed")
    observed_epoch()
    return result
