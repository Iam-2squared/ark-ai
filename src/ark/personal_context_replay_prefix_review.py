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
_DENIAL_NAMES = (
    "historical_writer_authenticated", "independent_custody_proven",
    "consent_verified", "revocation_freshness_verified",
    "context_disclosure_authorized", "tool_dispatch_authorized",
    "automatic_replay_authorized",
)
_ORIGINAL_DENIALS = tuple(vars(_RESULT)[key] for key in _DENIAL_NAMES)
# An exact frozen/slotted result can still execute newly installed field
# descriptors, lookup hooks, or a counterfeit constructor. Capture these
# originals before reading any retained witness or building a review.
_RESULT_FIELDS = (
    "retained_count", "current_count", "status",
    "current_chain_sha256", "review_sha256",
)
_RESULT_HOOKS = ("__init__", "__new__", "__getattribute__", "__getattr__")
_ORIGINAL_RESULT_FIELDS = tuple(vars(_RESULT)[name] for name in _RESULT_FIELDS)
_ORIGINAL_RESULT_HOOKS = tuple(
    vars(_RESULT).get(name) for name in _RESULT_HOOKS
)
# The review digest covers synthetic but linkable context request metadata.
# Pin primitives before retained-data access, SQLite, and every callback boundary.
_ORIGINAL_HASHLIB = hashlib
_ORIGINAL_SHA256 = hashlib.sha256
_ORIGINAL_JSON = json
_ORIGINAL_JSON_DUMPS = json.dumps
_ORIGINAL_DOMAIN = _DOMAIN


def _original_result_authority() -> None:
    # Reject substituted SHA/JSON before reading any retained context witness.
    if (
        hashlib is not _ORIGINAL_HASHLIB
        or hashlib.sha256 is not _ORIGINAL_SHA256
        or json is not _ORIGINAL_JSON
        or json.dumps is not _ORIGINAL_JSON_DUMPS
        or _DOMAIN is not _ORIGINAL_DOMAIN
    ):
        raise OfflineContextPrefixRejected(
            "context prefix digest implementation changed"
        )
    # Verify class descriptors without running any possibly replaced getter.
    # A counterfeit False callback remains executable code, not a denial.
    if (
        OfflineContextPrefixReview is not _RESULT
        or any(
            vars(_RESULT).get(name) is not original
            for names, originals in (
                (_RESULT_FIELDS, _ORIGINAL_RESULT_FIELDS),
                (_RESULT_HOOKS, _ORIGINAL_RESULT_HOOKS),
            )
            for name, original in zip(names, originals, strict=True)
        )
        or any(
            vars(_RESULT).get(key) is not original
            for key, original in zip(_DENIAL_NAMES, _ORIGINAL_DENIALS, strict=True)
        )
    ):
        raise OfflineContextPrefixRejected(
            "context result authority changed after denial"
        )


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
    _original_result_authority()
    try:
        previous = replay._check_witness(retained)
    except replay.OfflineContextReplayRejected as exc:
        raise OfflineContextPrefixRejected("invalid retained context witness") from exc
    # Preserve exact retained-witness failure precedence without reading any
    # counterfeit result authority getter. Still before all SQLite I/O.
    _original_result_authority()
    old_count, old_chain = previous
    path = ledger._path

    def stable() -> None:
        _original_result_authority()
        if (
            type(ledger) is not _LEDGER
            or ledger._path is not path
            or type(retained) is not _WITNESS
            or retained.count is not old_count
            or retained.chain_sha256 is not old_chain
            or replay._check_witness(retained) != previous
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
    _original_result_authority()
    result = _RESULT(old_count, current_epoch[0], status, current_epoch[1], digest)
    _original_result_authority()
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
        raise OfflineContextPrefixRejected("context replay result acquired authority")
    for name in _DENIAL_NAMES:
        _original_result_authority()
        if getattr(result, name) is not False:
            raise OfflineContextPrefixRejected("context replay result acquired authority")
        _original_result_authority()
    stable()
    # The last denied-authority property is a callback. A False getter can
    # still rewrite a previously checked count, status or permission flag,
    # and the retained-witness getter in stable() may run afterward too.
    # Recheck ALL result fields and denied authorities after those callbacks.
    def result_stable() -> None:
        _original_result_authority()
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
        ):
            raise OfflineContextPrefixRejected(
                "context result changed after denial"
            )
        for name in _DENIAL_NAMES:
            _original_result_authority()
            if getattr(result, name) is not False:
                raise OfflineContextPrefixRejected("context result changed after denial")
            _original_result_authority()

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
    _original_result_authority()
    stable()
    return result
