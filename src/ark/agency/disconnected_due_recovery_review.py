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

from . import disconnected_due_reservation as due_module
from .disconnected_due_prefix_review import (
    DisconnectedDuePrefixRejected,
    DisconnectedDuePrefixReview,
    review_retained_due_prefix,
)
from .disconnected_due_reservation import (
    DisconnectedDueReservations,
    DueReservationWitness,
)

_SHA = re.compile(r"[0-9a-f]{64}\Z")
_MAX_ROWS = 512
_DOMAIN = b"ARK-due-restart-triage-v2\0"
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
_RESULT_DENIALS = (
    "historical_prefix_proven", "independently_custodied",
    "trusted_clock_verified", "notification_authorized",
    "tool_dispatch_authorized", "automatic_replay_authorized",
)
_PREFIX_DENIALS = (
    "independently_authenticated", "historical_writer_proven",
    "trusted_clock_verified", "notification_authorized",
    "tool_dispatch_authorized", "automatic_replay_authorized",
)
_ORIGINAL_RESULT_DENIALS = tuple(
    getattr(_RESULT_TYPE, name) for name in _RESULT_DENIALS
)
_ORIGINAL_PREFIX_DENIALS = tuple(
    getattr(DisconnectedDuePrefixReview, name) for name in _PREFIX_DENIALS
)
_ORIGINAL_WITNESS_DENIAL = vars(_WITNESS_TYPE)["independent_custody_proven"]
_WITNESS_FIELDS = ("count", "fingerprint")
_WITNESS_HOOKS = ("__init__", "__new__", "__getattribute__", "__getattr__")
_ORIGINAL_WITNESS_FIELDS = tuple(
    vars(_WITNESS_TYPE)[name] for name in _WITNESS_FIELDS
)
_ORIGINAL_WITNESS_HOOKS = tuple(
    vars(_WITNESS_TYPE).get(name) for name in _WITNESS_HOOKS
)


def _require_original_witness_carrier() -> None:
    # The witness is a reflectively mutable, frozen dataclass. Validate its
    # descriptors BEFORE reading even one untrusted scalar: a substituted
    # descriptor can execute code before any type/digest comparison.
    if (
        due_module.DueReservationWitness is not _WITNESS_TYPE
        or any(
            vars(_WITNESS_TYPE).get(name) is not original
            for name, original in zip(
                _WITNESS_FIELDS, _ORIGINAL_WITNESS_FIELDS, strict=True,
            )
        )
        or any(
            vars(_WITNESS_TYPE).get(name) is not original
            for name, original in zip(
                _WITNESS_HOOKS, _ORIGINAL_WITNESS_HOOKS, strict=True,
            )
        )
        or vars(_WITNESS_TYPE).get("independent_custody_proven")
        is not _ORIGINAL_WITNESS_DENIAL
    ):
        raise DisconnectedDueRecoveryRejected("due witness carrier changed")


def _checked(value: object) -> tuple[int, str]:
    _require_original_witness_carrier()
    if (
        type(value) is not _WITNESS_TYPE
        or type(value.count) is not int
        or not 0 <= value.count <= _MAX_ROWS
        or type(value.fingerprint) is not str
        or _SHA.fullmatch(value.fingerprint) is None
        or _WITNESS_TYPE.independent_custody_proven
        is not _ORIGINAL_WITNESS_DENIAL
        or value.independent_custody_proven is not False
    ):
        raise DisconnectedDueRecoveryRejected("invalid exact due witness")
    _require_original_witness_carrier()
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

    # A later, locally well-formed append cannot justify changing a reserved
    # occurrence from the independently retained prefix. Reconcile that prefix
    # against ONE SQLite read transaction in the companion passive reviewer.
    # This second read must also agree with our earlier observation: concurrent
    # appends between reads are an ambiguity, not permission to continue.
    try:
        prefix = review_retained_due_prefix(ledger, retained)
    except DisconnectedDuePrefixRejected as exc:
        raise DisconnectedDueRecoveryRejected(
            "retained due reservation prefix rejected"
        ) from exc
    observed_epoch()
    expected_prefix_status = (
        "ADVANCED_PREFIX_UNAUTHENTICATED"
        if current[0] > prior[0] else "UNCHANGED_LOCAL_HISTORY"
    )
    if (
        type(prefix) is not DisconnectedDuePrefixReview
        or type(prefix.previous_count) is not int
        or prefix.previous_count != prior[0]
        or type(prefix.current_count) is not int
        or prefix.current_count != current[0]
        or type(prefix.current_fingerprint) is not str
        or prefix.current_fingerprint != current[1]
        or prefix.status != expected_prefix_status
        or prefix.independently_authenticated is not False
        or prefix.historical_writer_proven is not False
        or prefix.trusted_clock_verified is not False
        or prefix.notification_authorized is not False
        or prefix.tool_dispatch_authorized is not False
        or prefix.automatic_replay_authorized is not False
        or any(
            getattr(DisconnectedDuePrefixReview, name) is not original
            for name, original in zip(
                _PREFIX_DENIALS, _ORIGINAL_PREFIX_DENIALS, strict=True,
            )
        )
    ):
        raise DisconnectedDueRecoveryRejected(
            "due restart observation drifted or prefix gained authority"
        )
    observed_epoch()
    prefix_epoch = (
        prefix.previous_count, prefix.current_count,
        prefix.current_fingerprint, prefix.status, prefix.review_sha256,
    )

    def stable_prefix() -> None:
        if (
            type(prefix) is not DisconnectedDuePrefixReview
            or type(prefix.review_sha256) is not str
            or _SHA.fullmatch(prefix.review_sha256) is None
            or any(now is not original for now, original in zip(
                (
                    prefix.previous_count, prefix.current_count,
                    prefix.current_fingerprint, prefix.status, prefix.review_sha256,
                ), prefix_epoch, strict=True,
            ))
            or any(
                getattr(DisconnectedDuePrefixReview, name) is not original
                for name, original in zip(
                    _PREFIX_DENIALS, _ORIGINAL_PREFIX_DENIALS, strict=True,
                )
            )
        ):
            raise DisconnectedDueRecoveryRejected("retained prefix result changed")

    status = (
        "ADVANCED_HISTORY_UNVERIFIED"
        if current[0] > prior[0] else "UNCHANGED_LOCAL_HISTORY"
    )
    # Commit the independently re-read prefix receipt into this recovery
    # fingerprint. Counts and a tip hash omit the prefix review identity.
    # This is still only a *local* claim, never authenticated history.
    observed_epoch()
    stable_prefix()
    payload = json.dumps(
        (prior, current, status, prefix_epoch[4]),
        separators=(",", ":"), ensure_ascii=True,
    ).encode("ascii")
    observed_epoch()
    stable_prefix()
    digest = hashlib.sha256(_DOMAIN + payload).hexdigest()
    observed_epoch()
    stable_prefix()
    result = DisconnectedDueRecoveryReview(prior[0], current[0], status, digest)
    result_epoch = (prior[0], current[0], status, digest)

    def stable_result() -> None:
        observed_epoch()
        stable_prefix()
        if (
            type(result) is not _RESULT_TYPE
            or any(now is not original for now, original in zip(
                (result.previous_count, result.observed_count,
                 result.status, result.digest), result_epoch, strict=True,
            ))
            or any(
                getattr(_RESULT_TYPE, name) is not original
                for name, original in zip(
                    _RESULT_DENIALS, _ORIGINAL_RESULT_DENIALS, strict=True,
                )
            )
        ):
            raise DisconnectedDueRecoveryRejected("due recovery result changed")

    stable_result()
    for name in _RESULT_DENIALS:
        if getattr(result, name) is not False:
            raise DisconnectedDueRecoveryRejected("due recovery result changed")
        # Each denial getter is a callback boundary. A late False result
        # cannot conceal mutated fields, swapped descriptors, or changed
        # retained/reobserved SQLite witnesses.
        stable_result()
    stable_result()
    return result
