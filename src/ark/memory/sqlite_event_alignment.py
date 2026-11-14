"""Read-only reconciliation of local Memory v1 rows against event transitions.

This is an offline consistency audit, not signed provenance, user consent,
secure erasure, or a permission to access remembered content. The complete
scan is bounded and uses one SQLite read transaction. It never repairs data.
"""

from __future__ import annotations

import hashlib
import json
import sqlite3
from contextlib import closing
from dataclasses import dataclass

from .contracts import MemorySchemaError, MemoryScope
from .sqlite_store import SQLiteMemoryStore, _record, _validate_v1_schema

_MAX_ROWS = 10_000
_MAX_EVENTS = 40_000
_DOMAIN = b"ARK-memory-local-row-event-alignment-v1\0"


class MemoryEventAlignmentRejected(MemorySchemaError):
    """Local rows and recorded Memory v1 transitions do not reconcile."""


@dataclass(frozen=True, slots=True)
class MemoryEventAlignmentReview:
    row_count: int
    event_count: int
    scope_count: int
    last_event_id: int
    digest: str

    @property
    def independently_authenticated(self) -> bool:
        return False

    @property
    def user_consent_verified(self) -> bool:
        return False

    @property
    def deletion_or_erasure_proven(self) -> bool:
        return False

    @property
    def action_authorized(self) -> bool:
        return False


_REVIEW_TYPE = MemoryEventAlignmentReview
_ORIGINAL_REVIEW_INIT = vars(_REVIEW_TYPE)["__init__"]
# The review is an inert carrier. Never run substituted slot descriptors or
# lookup/constructor hooks while constructing or reading its audit digest.
_REVIEW_FIELDS = ("row_count", "event_count", "scope_count", "last_event_id", "digest")
_REVIEW_HOOKS = ("__new__", "__getattribute__", "__getattr__")
_ORIGINAL_REVIEW_FIELDS = tuple(vars(_REVIEW_TYPE)[name] for name in _REVIEW_FIELDS)
_ORIGINAL_REVIEW_HOOKS = tuple(vars(_REVIEW_TYPE).get(name) for name in _REVIEW_HOOKS)
_STORE_TYPE = SQLiteMemoryStore
_DENIAL_NAMES = (
    "independently_authenticated", "user_consent_verified",
    "deletion_or_erasure_proven", "action_authorized",
)
_ORIGINAL_DENIALS = tuple(vars(_REVIEW_TYPE)[name] for name in _DENIAL_NAMES)
_ORIGINAL_HASHLIB = hashlib
_ORIGINAL_JSON = json
_ORIGINAL_SHA256 = hashlib.sha256
_ORIGINAL_DUMPS = json.dumps
_ORIGINAL_DOMAIN = _DOMAIN


def _require_original_digest_callbacks() -> None:
    # Private local metadata and event identities must never enter an
    # unreviewed hash/JSON callback, including after reentrant row decoding.
    # Identity checks must also reject a whole-module rebinding and an
    # equal-byte hash-domain replacement. The scan budgets intentionally
    # remain injectable for existing bounded-failure tests.
    if (
        hashlib is not _ORIGINAL_HASHLIB
        or json is not _ORIGINAL_JSON
        or hashlib.sha256 is not _ORIGINAL_SHA256
        or json.dumps is not _ORIGINAL_DUMPS
        or _DOMAIN is not _ORIGINAL_DOMAIN
    ):
        raise MemoryEventAlignmentRejected("Memory audit digest authority changed")




def _require_original_denials() -> None:
    _require_original_digest_callbacks()
    # A newly-installed False-only property is not the reviewed authority
    # contract. Preserve the original descriptors across callbacks.
    if (
        MemoryEventAlignmentReview is not _REVIEW_TYPE
        or vars(_REVIEW_TYPE).get("__init__") is not _ORIGINAL_REVIEW_INIT
        or any(
            vars(_REVIEW_TYPE).get(name) is not original
            for name, original in zip(
                _REVIEW_FIELDS, _ORIGINAL_REVIEW_FIELDS, strict=True,
            )
        )
        or any(
            vars(_REVIEW_TYPE).get(name) is not original
            for name, original in zip(
                _REVIEW_HOOKS, _ORIGINAL_REVIEW_HOOKS, strict=True,
            )
        )
        or any(
            vars(_REVIEW_TYPE).get(name) is not original
            for name, original in zip(
                _DENIAL_NAMES, _ORIGINAL_DENIALS, strict=True,
            )
        )
    ):
        raise MemoryEventAlignmentRejected("Memory audit authority epoch changed")


def _charge(digest: object, entry: tuple[object, ...]) -> None:
    _require_original_denials()
    digest.update(
        json.dumps(entry, ensure_ascii=True, separators=(",", ":")).encode("ascii") + b"\n"
    )


def review_memory_event_alignment(
    store: SQLiteMemoryStore,
) -> MemoryEventAlignmentReview:
    """Inspect all scopes without returning their contents or changing SQLite.

    A CREATE starts revision 1, UPDATE must advance by exactly one, and a
    DELETE/EXPIRE closes the preceding active revision. A later CREATE may
    start a new lifecycle. The latest lifecycle must agree with live rows.

    Hash-consistent rewriting of both tables remains undetectable without a
    separately authenticated history witness.
    """
    _require_original_denials()
    if type(store) is not _STORE_TYPE:
        raise MemoryEventAlignmentRejected("exact local Memory store required")
    path = store.path
    if type(path) is not type(store.path):
        raise MemoryEventAlignmentRejected("invalid Memory source path")

    def stable_source() -> None:
        _require_original_denials()
        if type(store) is not _STORE_TYPE or store.path is not path:
            raise MemoryEventAlignmentRejected("Memory source changed during audit")

    digest = hashlib.sha256(_DOMAIN)
    stable_source()
    try:
        with closing(store._connect_readonly()) as conn:
            stable_source()
            conn.execute("BEGIN")
            try:
                _validate_v1_schema(conn)
                stable_source()
                current: dict[str, tuple[str, str, int, int, int]] = {}
                scopes: set[tuple[str, str]] = set()
                rows = 0
                for row in conn.execute("SELECT * FROM memories ORDER BY memory_id"):
                    rows += 1
                    if rows > _MAX_ROWS:
                        raise MemoryEventAlignmentRejected("Memory audit row budget exceeded")
                    record = _record(row)
                    stable_source()
                    if record.memory_id in current:
                        raise MemoryEventAlignmentRejected("duplicate live memory identity")
                    owner, namespace = record.scope.owner_id, record.scope.namespace
                    current[record.memory_id] = (
                        owner, namespace, record.revision,
                        record.created_at_ms, record.updated_at_ms,
                    )
                    scopes.add((owner, namespace))
                    # A snapshot fingerprint must cover the entire validated
                    # persisted row, not just the identity/revision/content
                    # digest. Otherwise expiry, metadata, or timestamps could
                    # change while the audit fingerprint stayed identical.
                    # Only a SHA-256 commitment, never plaintext metadata,
                    # is included in the returned review.
                    metadata_sha = hashlib.sha256(
                        row["metadata_json"].encode("utf-8")
                    ).hexdigest()
                    _charge(digest, (
                        "row", record.memory_id, owner, namespace, record.source_id,
                        record.revision, record.content_sha256, metadata_sha,
                        record.created_at_ms, record.updated_at_ms,
                        record.expires_at_ms,
                    ))
                # Persisted v1 event times must reconcile with the live row's
                # current lifetime, not merely its final revision. The
                # clock is caller-supplied and need not be monotonic, so do
                # not require chronological event timestamps.
                lifecycle: dict[str, tuple[str, str, int, bool, int, int]] = {}
                count = 0
                last_id = 0
                for event in conn.execute(
                    "SELECT event_id,memory_id,owner_id,namespace,operation,"
                    "revision,occurred_at_ms FROM memory_events ORDER BY event_id"
                ):
                    count += 1
                    if count > _MAX_EVENTS:
                        raise MemoryEventAlignmentRejected("Memory audit event budget exceeded")
                    event_id, memory_id, owner, namespace, operation, revision, at = event
                    if (
                        type(event_id) is not int or event_id <= last_id
                        or type(memory_id) is not str
                        or len(memory_id) != 68 or not memory_id.startswith("mem_")
                        or any(c not in "0123456789abcdef" for c in memory_id[4:])
                        or type(revision) is not int or not 1 <= revision <= (1 << 63) - 1
                        or type(at) is not int or not 0 <= at <= (1 << 63) - 1
                        or type(operation) is not str
                        or operation not in {"create", "update", "delete", "expire"}
                    ):
                        raise MemoryEventAlignmentRejected("invalid stored Memory event")
                    # Event IDs are global AUTOINCREMENT values in the
                    # append-only v1 journal. Reviewing every scope from
                    # genesis must not silently accept a missing first or
                    # middle event after both a row and its history were
                    # removed. A retained independent witness is still
                    # needed to detect a truncated suffix or valid rewrite.
                    if event_id != last_id + 1:
                        raise MemoryEventAlignmentRejected(
                            "Memory event ID gap in append-only history"
                        )
                    try:
                        scoped = MemoryScope(owner, namespace)
                    except (ValueError, TypeError) as exc:
                        raise MemoryEventAlignmentRejected("invalid event scope") from exc
                    if type(scoped.owner_id) is not str or type(scoped.namespace) is not str:
                        raise MemoryEventAlignmentRejected("invalid event scope carriers")
                    previous = lifecycle.get(memory_id)
                    if previous is not None and previous[:2] != (owner, namespace):
                        raise MemoryEventAlignmentRejected("Memory identity changed scope")
                    if operation == "create":
                        if revision != 1 or previous is not None and previous[3]:
                            raise MemoryEventAlignmentRejected("invalid Memory creation history")
                        active = True
                        created_at = at
                        last_write_at = at
                    else:
                        if previous is None or not previous[3]:
                            raise MemoryEventAlignmentRejected("event without active Memory")
                        wanted = previous[2] + (operation == "update")
                        if revision != wanted:
                            raise MemoryEventAlignmentRejected("Memory revision history differs")
                        active = operation == "update"
                        created_at = previous[4]
                        last_write_at = at if active else previous[5]
                    lifecycle[memory_id] = (
                        owner, namespace, revision, active, created_at, last_write_at,
                    )
                    scopes.add((owner, namespace))
                    last_id = event_id
                    _charge(digest, (
                        "event", event_id, memory_id, owner, namespace, operation, revision, at,
                    ))
                    stable_source()
                for memory_id, state in lifecycle.items():
                    expected = current.pop(memory_id, None)
                    if state[3]:
                        if expected != (
                            state[0], state[1], state[2], state[4], state[5],
                        ):
                            raise MemoryEventAlignmentRejected(
                                "live Memory row/time lacks matching event"
                            )
                    elif expected is not None:
                        raise MemoryEventAlignmentRejected("terminal Memory still has a row")
                if current:
                    raise MemoryEventAlignmentRejected("live Memory has no creation event")
                # Dense surviving event IDs do not rule out deletion of the
                # final event (and corresponding row). SQLite AUTOINCREMENT's
                # committed high-water mark is an additional local signal,
                # checked inside this same read snapshot. An attacker able to
                # rewrite sqlite_sequence can still erase this indication;
                # an independently retained witness remains essential.
                sequences = conn.execute(
                    "SELECT seq FROM sqlite_sequence WHERE name='memory_events'"
                ).fetchall()
                if count == 0:
                    if sequences:
                        raise MemoryEventAlignmentRejected(
                            "Memory append-only event tail was truncated"
                        )
                elif (
                    len(sequences) != 1 or type(sequences[0][0]) is not int
                    or sequences[0][0] != last_id
                ):
                    # sqlite_sequence does not declare name UNIQUE. A
                    # correct-looking first row plus a forged second entry
                    # is ambiguous, even if fetchone() would return the
                    # expected high-water. Deny all duplicate markers.
                    raise MemoryEventAlignmentRejected(
                        "Memory append-only event high-water mark differs"
                    )
                stable_source()
                conn.commit()
            except BaseException:
                conn.rollback()
                raise
    except sqlite3.Error as exc:
        raise MemoryEventAlignmentRejected("Memory SQLite audit unavailable") from exc
    stable_source()
    _require_original_denials()
    expected = (rows, count, len(scopes), last_id, digest.hexdigest())
    review = MemoryEventAlignmentReview(*expected)

    def stable_report() -> bool:
        fields = (
            review.row_count, review.event_count, review.scope_count,
            review.last_event_id, review.digest,
        )
        return (
            type(review) is _REVIEW_TYPE
            and all(
                type(value) is type(original) and value == original
                for value, original in zip(fields, expected, strict=True)
            )
        )

    if not stable_report():
        raise MemoryEventAlignmentRejected("Memory audit result changed")
    for name in _DENIAL_NAMES:
        _require_original_denials()
        if not stable_report() or getattr(review, name) is not False:
            raise MemoryEventAlignmentRejected("Memory audit result acquired authority")
        # Original False-only getters must not conceal reentrant mutation of
        # the returned row-count or fingerprint after the initial checks.
        if not stable_report():
            raise MemoryEventAlignmentRejected("Memory audit result changed")
    _require_original_denials()
    stable_source()
    if not stable_report():
        raise MemoryEventAlignmentRejected("Memory audit result changed")
    return review
