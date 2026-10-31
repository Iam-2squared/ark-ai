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
_STORE_TYPE = SQLiteMemoryStore


def _charge(digest: object, entry: tuple[object, ...]) -> None:
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
    if type(store) is not _STORE_TYPE:
        raise MemoryEventAlignmentRejected("exact local Memory store required")
    path = store.path
    if type(path) is not type(store.path):
        raise MemoryEventAlignmentRejected("invalid Memory source path")

    def stable_source() -> None:
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
                current: dict[str, tuple[str, str, int]] = {}
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
                    current[record.memory_id] = (owner, namespace, record.revision)
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
                lifecycle: dict[str, tuple[str, str, int, bool]] = {}
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
                    else:
                        if previous is None or not previous[3]:
                            raise MemoryEventAlignmentRejected("event without active Memory")
                        wanted = previous[2] + (operation == "update")
                        if revision != wanted:
                            raise MemoryEventAlignmentRejected("Memory revision history differs")
                        active = operation == "update"
                    lifecycle[memory_id] = (owner, namespace, revision, active)
                    scopes.add((owner, namespace))
                    last_id = event_id
                    _charge(digest, (
                        "event", event_id, memory_id, owner, namespace, operation, revision, at,
                    ))
                    stable_source()
                for memory_id, state in lifecycle.items():
                    expected = current.pop(memory_id, None)
                    if state[3]:
                        if expected != state[:3]:
                            raise MemoryEventAlignmentRejected("live Memory lacks matching event")
                    elif expected is not None:
                        raise MemoryEventAlignmentRejected("terminal Memory still has a row")
                if current:
                    raise MemoryEventAlignmentRejected("live Memory has no creation event")
                stable_source()
                conn.commit()
            except BaseException:
                conn.rollback()
                raise
    except sqlite3.Error as exc:
        raise MemoryEventAlignmentRejected("Memory SQLite audit unavailable") from exc
    stable_source()
    review = MemoryEventAlignmentReview(rows, count, len(scopes), last_id, digest.hexdigest())
    if (
        type(review) is not _REVIEW_TYPE
        or type(review.row_count) is not int or review.row_count != rows
        or type(review.event_count) is not int or review.event_count != count
        or type(review.scope_count) is not int or review.scope_count != len(scopes)
        or type(review.last_event_id) is not int or review.last_event_id != last_id
        or type(review.digest) is not str or review.digest != digest.hexdigest()
        or review.independently_authenticated is not False
        or review.user_consent_verified is not False
        or review.deletion_or_erasure_proven is not False
        or review.action_authorized is not False
    ):
        raise MemoryEventAlignmentRejected("Memory audit result acquired authority")
    stable_source()
    return review
