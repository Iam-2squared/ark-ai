"""One-transaction retained-prefix diagnosis for offline Context requests.

The stored SHA chain is content-free but linkable metadata. This opt-in
review detects rewriting an OLD local prefix even after further requests
were appended. It does not authenticate independent custody, consent,
revocation freshness, disclosure or permission to execute anything.
"""

from __future__ import annotations

import hashlib
import json
import sqlite3
from contextlib import closing
from dataclasses import dataclass

from . import personal_context_replay_ledger as replay


class OfflineContextPrefixRejected(ValueError):
    """Previous synthetic context request history does not match SQLite."""


@dataclass(frozen=True, slots=True)
class OfflineContextPrefixReview:
    retained_count: int
    current_count: int
    status: str
    current_chain_sha256: str
    review_sha256: str

    @property
    def historical_writer_authenticated(self) -> bool:
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


_DOMAIN = b"ARK-disconnected-context-retained-prefix-v1\0"
_LEDGER = replay.DisconnectedContextReplayLedger
_WITNESS = replay.OfflineContextReplayWitness
_RESULT = OfflineContextPrefixReview


def review_retained_context_replay_prefix(
    ledger: replay.DisconnectedContextReplayLedger,
    retained: replay.OfflineContextReplayWitness,
) -> OfflineContextPrefixReview:
    """Verify the previous chain tip against the same validated current DB.

    With a complete checked SHA chain, the stored link at sequence N binds
    the entire original N-row prefix. Scanning this link and the current tip
    in one read transaction removes the two-snapshot race, but is not
    independent or cryptographically signed storage provenance.
    """
    if type(ledger) is not _LEDGER:
        raise OfflineContextPrefixRejected("exact offline context ledger required")
    try:
        previous = replay._check_witness(retained)
    except replay.OfflineContextReplayRejected as exc:
        raise OfflineContextPrefixRejected("invalid retained context witness") from exc
    old_count, old_chain = previous
    path = ledger._path

    def stable() -> None:
        if (
            type(ledger) is not _LEDGER
            or ledger._path is not path
            or type(retained) is not _WITNESS
            or retained.count is not old_count
            or retained.chain_sha256 is not old_chain
            or retained.independent_custody_proven is not False
        ):
            raise OfflineContextPrefixRejected("context source/witness changed during read")

    stable()
    try:
        with closing(ledger._open(read_only=True)) as conn:
            stable()
            conn.execute("BEGIN")
            try:
                observed = replay._inspect(conn)
                stable()
                if type(observed) is not _WITNESS:
                    raise OfflineContextPrefixRejected("invalid observed context witness")
                current_epoch = replay._check_witness(observed)
                if current_epoch[0] < old_count:
                    raise OfflineContextPrefixRejected("retained context prefix rolled back")
                if old_count == 0:
                    observed_prefix = replay.genesis_offline_context_replay_witness()
                    observed_chain = observed_prefix.chain_sha256
                else:
                    row = conn.execute(
                        "SELECT chain_sha256 FROM context_requests WHERE seq=?",
                        (old_count,),
                    ).fetchone()
                    observed_chain = row[0] if row is not None else None
                stable()
                if observed_chain != old_chain:
                    raise OfflineContextPrefixRejected("retained context prefix rewritten")
                conn.rollback()
            except BaseException:
                conn.rollback()
                raise
    except (sqlite3.Error, replay.OfflineContextReplayRejected) as exc:
        raise OfflineContextPrefixRejected(
            "context replay history unavailable"
        ) from exc

    stable()
    if (
        observed.count is not current_epoch[0]
        or observed.chain_sha256 is not current_epoch[1]
    ):
        raise OfflineContextPrefixRejected("current context witness changed")
    status = (
        "ADVANCED_PREFIX_UNAUTHENTICATED"
        if current_epoch[0] > old_count else "UNCHANGED_LOCAL_HISTORY"
    )
    encoded = json.dumps(
        (previous, current_epoch, status), ensure_ascii=True,
        separators=(",", ":"),
    ).encode("ascii")
    stable()
    digest = hashlib.sha256(_DOMAIN + encoded).hexdigest()
    stable()
    result = _RESULT(old_count, current_epoch[0], status, current_epoch[1], digest)
    if (
        type(result) is not _RESULT
        or type(result.retained_count) is not int
        or result.retained_count != old_count
        or type(result.current_count) is not int
        or result.current_count != current_epoch[0]
        or result.status is not status
        or result.current_chain_sha256 is not current_epoch[1]
        or result.review_sha256 is not digest
        or result.historical_writer_authenticated is not False
        or result.independent_custody_proven is not False
        or result.consent_verified is not False
        or result.revocation_freshness_verified is not False
        or result.context_disclosure_authorized is not False
        or result.tool_dispatch_authorized is not False
        or result.automatic_replay_authorized is not False
    ):
        raise OfflineContextPrefixRejected("context replay result acquired authority")
    stable()
    # The last denied-authority property is a callback. A False getter can
    # still rewrite a previously checked count, status or permission flag,
    # and the retained-witness getter in stable() may run afterward too.
    # Recheck ALL result fields and denied authorities after those callbacks.
    def result_stable() -> None:
        if (
            type(result) is not _RESULT
            or type(result.retained_count) is not int
            or result.retained_count != old_count
            or type(result.current_count) is not int
            or result.current_count != current_epoch[0]
            or type(result.status) is not str
            or result.status is not status
            or type(result.current_chain_sha256) is not str
            or result.current_chain_sha256 is not current_epoch[1]
            or type(result.review_sha256) is not str
            or result.review_sha256 is not digest
            or result.historical_writer_authenticated is not False
            or result.independent_custody_proven is not False
            or result.consent_verified is not False
            or result.revocation_freshness_verified is not False
            or result.context_disclosure_authorized is not False
            or result.tool_dispatch_authorized is not False
            or result.automatic_replay_authorized is not False
        ):
            raise OfflineContextPrefixRejected(
                "context result changed after denial"
            )

    result_stable()
    stable()
    # A denial getter may have returned False while replacing an earlier
    # carrier. A second scalar pass avoids returning that mixed result.
    if (
        type(result) is not _RESULT
        or type(result.retained_count) is not int
        or result.retained_count != old_count
        or type(result.current_count) is not int
        or result.current_count != current_epoch[0]
        or result.status is not status
        or result.current_chain_sha256 is not current_epoch[1]
        or result.review_sha256 is not digest
    ):
        raise OfflineContextPrefixRejected("context result changed after final review")
    return result
