"""Compare a retained Memory row/event snapshot with current local SQLite state.

A caller must keep the previous digest independently from this database.
This detects regressions and changes without appended events, but an attacker
controlling both the saved witness and SQLite can forge both. Appends do NOT
prove the authenticity of historical event prefixes or writer identities.
No Memory content is disclosed and no database mutations are performed.
"""

from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass

from .contracts import MemorySchemaError
from .sqlite_event_alignment import (
    MemoryEventAlignmentReview,
    review_memory_event_alignment,
)
from .sqlite_store import SQLiteMemoryStore

_SHA = re.compile(r"[0-9a-f]{64}\Z")
_MAX_ROWS = 10_000
_MAX_EVENTS = 40_000
_MAX_SQLITE_INTEGER = (1 << 63) - 1
_DOMAIN = b"ARK-retained-local-memory-alignment-comparison-v1\0"
_REVIEW = MemoryEventAlignmentReview


class MemoryAlignmentHistoryRejected(MemorySchemaError):
    """A retained Memory alignment witness cannot match the current history."""


@dataclass(frozen=True, slots=True)
class RetainedMemoryAlignmentComparison:
    previous_event_count: int
    current_event_count: int
    appended_event_count: int
    status: str
    comparison_sha256: str

    @property
    def historical_prefix_authenticated(self) -> bool:
        return False

    @property
    def writer_authenticated(self) -> bool:
        return False

    @property
    def content_disclosure_authorized(self) -> bool:
        return False

    @property
    def dispatch_authorized(self) -> bool:
        return False


_RESULT = RetainedMemoryAlignmentComparison


def _epoch(value: object) -> tuple[object, ...]:
    if type(value) is not _REVIEW:
        raise MemoryAlignmentHistoryRejected("exact retained local alignment required")
    epoch = (
        value.row_count, value.event_count, value.scope_count,
        value.last_event_id, value.digest,
    )
    rows, events, scopes, tail, digest = epoch
    if (
        type(rows) is not int or not 0 <= rows <= _MAX_ROWS
        or type(events) is not int or not 0 <= events <= _MAX_EVENTS
        or type(scopes) is not int or not 0 <= scopes <= _MAX_ROWS + _MAX_EVENTS
        or type(tail) is not int or not 0 <= tail <= _MAX_SQLITE_INTEGER
        or (events == 0 and tail != 0)
        or (events > 0 and tail < events)
        or type(digest) is not str or _SHA.fullmatch(digest) is None
        or value.independently_authenticated is not False
        or value.user_consent_verified is not False
        or value.deletion_or_erasure_proven is not False
        or value.action_authorized is not False
    ):
        raise MemoryAlignmentHistoryRejected("invalid alignment shape or authority")
    return epoch


def compare_retained_memory_alignment(
    store: SQLiteMemoryStore,
    retained: MemoryEventAlignmentReview,
) -> RetainedMemoryAlignmentComparison:
    """Reject local rollback or silent row changes, never attest a later append."""
    if type(store) is not SQLiteMemoryStore:
        raise MemoryAlignmentHistoryRejected("exact local SQLite source required")
    path = store.path
    previous = _epoch(retained)

    def stable() -> None:
        if (
            type(store) is not SQLiteMemoryStore or store.path is not path
            or type(retained) is not _REVIEW
            or any(current is not original for current, original in zip(
                _epoch(retained), previous, strict=True,
            ))
        ):
            raise MemoryAlignmentHistoryRejected("retained Memory epoch changed")

    stable()
    current_review = review_memory_event_alignment(store)
    stable()
    current = _epoch(current_review)
    old_rows, old_count, old_scopes, old_tail, old_digest = previous
    new_rows, new_count, new_scopes, new_tail, new_digest = current
    if (
        new_count < old_count
        or new_tail < old_tail
        or new_scopes < old_scopes
        or (new_count == old_count and new_tail != old_tail)
        or (new_count > old_count and new_tail <= old_tail)
    ):
        raise MemoryAlignmentHistoryRejected("local Memory event history regressed")
    if new_count == old_count and (
        new_rows != old_rows or new_digest != old_digest
    ):
        raise MemoryAlignmentHistoryRejected("Memory changed without appended history")
    appended = new_count - old_count
    status = (
        "ADVANCED_PREFIX_UNAUTHENTICATED" if appended else "UNCHANGED_LOCAL_HISTORY"
    )
    encoded = json.dumps(
        (previous, current, status), ensure_ascii=True, separators=(",", ":"),
    ).encode("ascii")
    stable()
    fingerprint = hashlib.sha256(_DOMAIN + encoded).hexdigest()
    stable()
    if any(actual is not pinned for actual, pinned in zip(
        _epoch(current_review), current, strict=True,
    )):
        raise MemoryAlignmentHistoryRejected("current alignment epoch changed")
    result = _RESULT(old_count, new_count, appended, status, fingerprint)
    if (
        type(result) is not _RESULT
        or result.previous_event_count is not old_count
        or result.current_event_count is not new_count
        or type(result.appended_event_count) is not int
        or result.appended_event_count != appended
        or result.status is not status
        or result.comparison_sha256 is not fingerprint
        or result.historical_prefix_authenticated is not False
        or result.writer_authenticated is not False
        or result.content_disclosure_authorized is not False
        or result.dispatch_authorized is not False
    ):
        raise MemoryAlignmentHistoryRejected("comparison result acquired authority")
    stable()
    return result
