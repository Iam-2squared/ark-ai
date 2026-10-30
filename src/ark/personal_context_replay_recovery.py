"""Read-only restart triage for synthetic Personal Context replay reservations.

A same-count local history change or rollback is refused. New append history is
UNVERIFIED: a local SQLite hash chain does not authenticate its writer or prove
retention, consent, revocation, deletion, external effect or historical prefix.
No real content is read, disclosed, deleted, scheduled or dispatched.
"""

from __future__ import annotations

import hashlib
import json
import re
import sqlite3
from contextlib import closing
from dataclasses import dataclass

from .personal_context_replay_ledger import (
    DisconnectedContextReplayLedger,
    OfflineContextReplayRejected,
    OfflineContextReplayWitness,
    _inspect,
)

_SHA = re.compile(r"[0-9a-f]{64}\Z")
_DOMAIN = b"ARK-offline-context-replay-restart-review-v1\0"
_LEDGER_TYPE = DisconnectedContextReplayLedger
_WITNESS_TYPE = OfflineContextReplayWitness


class OfflineContextRecoveryRejected(OfflineContextReplayRejected):
    """Local replay-recovery evidence cannot be interpreted safely."""


@dataclass(frozen=True, slots=True)
class OfflineContextRecoveryReview:
    retained_count: int
    observed_count: int
    status: str
    comparison_sha256: str

    @property
    def historical_prefix_proven(self) -> bool:
        return False

    @property
    def independent_custody_proven(self) -> bool:
        return False

    @property
    def consent_verified(self) -> bool:
        return False

    @property
    def revocation_freshness_verified(self) -> bool:
        return False

    @property
    def context_disclosure_authorized(self) -> bool:
        return False

    @property
    def tool_dispatch_authorized(self) -> bool:
        return False

    @property
    def automatic_replay_authorized(self) -> bool:
        return False


_RESULT_TYPE = OfflineContextRecoveryReview


def _witness_fields(value: object) -> tuple[int, str]:
    if (
        type(value) is not _WITNESS_TYPE
        or type(value.count) is not int
        or not 0 <= value.count <= 512
        or type(value.chain_sha256) is not str
        or _SHA.fullmatch(value.chain_sha256) is None
        or value.independent_custody_proven is not False
    ):
        raise OfflineContextRecoveryRejected("invalid exact context replay witness")
    return value.count, value.chain_sha256


def review_restarted_context_replay(
    ledger: DisconnectedContextReplayLedger,
    retained: OfflineContextReplayWitness,
) -> OfflineContextRecoveryReview:
    """Compare a locally retained witness with a fresh read-only SQLite view.

    The caller must store retained separately from the DB. An advancing history
    remains unverified even when both local objects pass structural checks.
    The result never authorizes replay or use of Personal Context.
    """
    if type(ledger) is not _LEDGER_TYPE:
        raise OfflineContextRecoveryRejected("exact disconnected context ledger required")
    pinned = _witness_fields(retained)
    pinned_path = ledger._path
    pinned_carrier = retained
    pinned_count, pinned_digest = retained.count, retained.chain_sha256

    def stable() -> None:
        if (
            type(ledger) is not _LEDGER_TYPE
            or ledger._path is not pinned_path
            or retained is not pinned_carrier
            or _witness_fields(retained) != pinned
            or retained.count is not pinned_count
            or retained.chain_sha256 is not pinned_digest
        ):
            raise OfflineContextRecoveryRejected("retained context replay witness changed")

    stable()
    observed = ledger.witness()
    stable()
    current = _witness_fields(observed)
    observed_count, observed_digest = observed.count, observed.chain_sha256

    def stable_observed() -> None:
        stable()
        if (
            type(observed) is not _WITNESS_TYPE
            or _witness_fields(observed) != current
            or observed.count is not observed_count
            or observed.chain_sha256 is not observed_digest
        ):
            raise OfflineContextRecoveryRejected("observed context replay witness changed")

    def verify_durable_tip() -> None:
        # witness() is a public, overridable callback. It can return a forged
        # or stale but exact-type result, including after an intervening SQLite
        # append. Read the real rows in a separate read-only transaction.
        stable_observed()
        try:
            with closing(ledger._open(read_only=True)) as conn:
                conn.execute("BEGIN")
                try:
                    durable = _inspect(conn)
                    stable_observed()
                    if _witness_fields(durable) != current:
                        raise OfflineContextRecoveryRejected(
                            "context replay durable tip differs from callback"
                        )
                    conn.commit()
                except BaseException:
                    conn.rollback()
                    raise
        except (sqlite3.Error, OfflineContextReplayRejected) as exc:
            if type(exc) is OfflineContextRecoveryRejected:
                raise
            raise OfflineContextRecoveryRejected(
                "context replay durable tip cannot be verified"
            ) from exc
        stable_observed()

    verify_durable_tip()
    if current[0] < pinned[0]:
        raise OfflineContextRecoveryRejected("context replay history count regressed")
    if current[0] == pinned[0] and current[1] != pinned[1]:
        raise OfflineContextRecoveryRejected("context replay history rewritten at same count")
    status = (
        "ADVANCED_HISTORY_UNVERIFIED"
        if current[0] > pinned[0]
        else "UNCHANGED_LOCAL_HISTORY"
    )
    payload = json.dumps(
        (pinned, current, status),
        separators=(",", ":"), ensure_ascii=True,
    ).encode("ascii")
    stable_observed()
    digest = hashlib.sha256(_DOMAIN + payload).hexdigest()
    stable_observed()
    result = OfflineContextRecoveryReview(pinned[0], current[0], status, digest)
    stable_observed()
    if (
        type(result) is not _RESULT_TYPE
        or type(result.retained_count) is not int
        or result.retained_count != pinned[0]
        or type(result.observed_count) is not int
        or result.observed_count != current[0]
        or type(result.status) is not str
        or result.status is not status
        or type(result.comparison_sha256) is not str
        or result.comparison_sha256 is not digest
        or result.historical_prefix_proven is not False
        or result.independent_custody_proven is not False
        or result.consent_verified is not False
        or result.revocation_freshness_verified is not False
        or result.context_disclosure_authorized is not False
        or result.tool_dispatch_authorized is not False
        or result.automatic_replay_authorized is not False
    ):
        raise OfflineContextRecoveryRejected("context replay review result changed")
    verify_durable_tip()
    return result
