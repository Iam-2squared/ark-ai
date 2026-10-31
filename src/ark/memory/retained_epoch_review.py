"""Compare two separately retained local Memory epochs without granting authority.

Requires independently retained caller snapshots. It rejects regressions and
undocumented same-tail edits but cannot attest the historical prefix after a
legitimate append, storage-writer identity, consent, or real-world actions.
"""

from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass

from .atomic_epoch_review import AtomicMemoryEpochReview
from .contracts import MemorySchemaError

_SHA = re.compile(r"[0-9a-f]{64}\Z")
_DOMAIN = b"ARK-memory-retained-epoch-comparison-v1\0"
_REVIEW_TYPE = AtomicMemoryEpochReview
_MAX_ROWS = 10_000
_MAX_EVENTS = 10_000
_SQLITE_MAX = 2**63 - 1


@dataclass(frozen=True, slots=True)
class RetainedMemoryEpochComparison:
    scope_fingerprints: tuple[str, ...]
    new_event_counts: tuple[int, ...]
    status: str
    comparison_digest: str

    @property
    def historical_prefix_proven(self) -> bool:
        return False

    @property
    def independent_writer_proven(self) -> bool:
        return False

    @property
    def custody_authenticated(self) -> bool:
        return False

    @property
    def dispatch_authorized(self) -> bool:
        return False

    @property
    def memory_disclosure_authorized(self) -> bool:
        return False


_COMPARISON_TYPE = RetainedMemoryEpochComparison


def _validate(review: object) -> tuple[object, ...]:
    if type(review) is not _REVIEW_TYPE:
        raise MemorySchemaError("exact retained Memory review required")
    fields = (
        review.scope_fingerprints, review.row_counts, review.event_counts,
        review.event_tail_ids, review.epoch_digest, review.content_digest,
    )
    scopes, rows, events, tails, epoch_digest, content_digest = fields
    if (
        type(scopes) is not tuple
        or not 1 <= len(scopes) <= 8
        or any(type(value) is not str or _SHA.fullmatch(value) is None for value in scopes)
        or len(set(scopes)) != len(scopes)
        or any(type(value) is not tuple or len(value) != len(scopes)
               for value in (rows, events, tails))
        or type(epoch_digest) is not str or _SHA.fullmatch(epoch_digest) is None
        or type(content_digest) is not str or _SHA.fullmatch(content_digest) is None
        or review.independent_writer_proven is not False
        or review.cross_store_atomicity_proven is not False
        or review.trusted_clock_proven is not False
        or review.memory_disclosure_authorized is not False
        or review.dispatch_authorized is not False
    ):
        raise MemorySchemaError("invalid retained Memory epoch shape or authority")
    for row_count, event_count, tail in zip(rows, events, tails, strict=True):
        if (
            type(row_count) is not int or not 0 <= row_count <= _MAX_ROWS
            or type(event_count) is not int or not 0 <= event_count <= _MAX_EVENTS
            or type(tail) is not int or not 0 <= tail <= _SQLITE_MAX
            or (event_count == 0 and tail != 0)
            or (event_count > 0 and tail < event_count)
        ):
            raise MemorySchemaError("invalid retained Memory event counts")
    return fields


def review_retained_memory_epoch(
    previous: AtomicMemoryEpochReview, current: AtomicMemoryEpochReview,
) -> RetainedMemoryEpochComparison:
    """Reject local evidence regression; never claim append-prefix authenticity.

    Same event counts and tail IDs MUST have identical metadata/event content
    across observations even when the observation clock moved forward. A larger
    tail is marked UNVERIFIED, since a malicious replacement with extra events
    cannot be ruled out by an in-database hash.
    """
    if previous is current:
        raise MemorySchemaError("two independent Memory observations required")
    original_previous = _validate(previous)
    original_current = _validate(current)

    def stable() -> None:
        if (
            type(previous) is not _REVIEW_TYPE
            or type(current) is not _REVIEW_TYPE
            or any(now is not old for now, old in zip(
                _validate(previous), original_previous, strict=True,
            ))
            or any(now is not old for now, old in zip(
                _validate(current), original_current, strict=True,
            ))
        ):
            raise MemorySchemaError("retained Memory carriers changed during comparison")

    stable()
    scopes_p, rows_p, counts_p, tails_p, _clock_p, digest_p = original_previous
    scopes_c, _rows_c, counts_c, tails_c, _clock_c, digest_c = original_current
    if scopes_p != scopes_c:
        raise MemorySchemaError("retained Memory scope identity changed")
    growth = []
    for count_p, tail_p, count_c, tail_c in zip(
        counts_p, tails_p, counts_c, tails_c, strict=True,
    ):
        if count_c < count_p or tail_c < tail_p:
            raise MemorySchemaError("retained Memory history regressed")
        if count_c == count_p and tail_c != tail_p:
            raise MemorySchemaError("retained Memory event tail replaced")
        if count_c > count_p and tail_c <= tail_p:
            raise MemorySchemaError("retained Memory event tail did not advance")
        growth.append(count_c - count_p)
    if not any(growth) and (digest_p != digest_c or rows_p != original_current[1]):
        raise MemorySchemaError("retained Memory content changed without event")
    status = "ADVANCED_HISTORY_UNVERIFIED" if any(growth) else "UNCHANGED_LOCAL_CONTENT"
    growth_tuple = tuple(growth)
    packed = json.dumps(
        (scopes_p, counts_p, tails_p, digest_p, counts_c, tails_c,
         digest_c, status),
        separators=(",", ":"), ensure_ascii=True,
    ).encode("ascii")
    stable()
    fingerprint = hashlib.sha256(_DOMAIN + packed).hexdigest()
    stable()
    result = RetainedMemoryEpochComparison(scopes_p, growth_tuple, status, fingerprint)
    stable()
    if (
        type(result) is not _COMPARISON_TYPE
        or result.scope_fingerprints is not scopes_p
        or result.new_event_counts is not growth_tuple
        or result.status is not status
        or result.comparison_digest is not fingerprint
        or result.historical_prefix_proven is not False
        or result.independent_writer_proven is not False
        or result.custody_authenticated is not False
        or result.dispatch_authorized is not False
        or result.memory_disclosure_authorized is not False
    ):
        raise MemorySchemaError("retained Memory comparison result changed")
    return result
