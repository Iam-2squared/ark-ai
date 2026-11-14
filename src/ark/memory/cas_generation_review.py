"""Read-only diagnostic for Memory v1 revision reuse across lifetimes.

A CAS revision is scoped to a live SQLite row, not authenticated ownership of
the row's earlier lifetime. When a deterministic ID is deleted and recreated,
revision 1 can recur. This diagnostic explicitly flags that ABA ambiguity.
It never executes a write, authorizes erasure or authenticates a writer.
"""

from __future__ import annotations

import hashlib
import json
import sqlite3
from contextlib import closing
from dataclasses import dataclass

from .contracts import MemorySchemaError, MemoryScope
from .sqlite_store import (
    SQLITE_INT_MAX,
    SQLiteMemoryStore,
    _record,
    _validate_v1_schema,
    deterministic_memory_id,
)

_MAX_EVENTS = 40_000
_DOMAIN = b"ARK-readonly-memory-generation-ambiguity-v1\0"
_FLAGS = ("write_authorized", "erase_authorized", "generation_authenticated")


class MemoryGenerationReviewRejected(MemorySchemaError):
    """The local Memory generation evidence could not be safely reconciled."""


@dataclass(frozen=True, slots=True)
class MemoryGenerationReview:
    memory_id: str
    event_count: int
    generation_count: int
    live_revision: int | None
    expected_revision: int
    revision_reuse_possible: bool
    retained_history_sha256: str

    @property
    def write_authorized(self) -> bool:
        return False

    @property
    def erase_authorized(self) -> bool:
        return False

    @property
    def generation_authenticated(self) -> bool:
        return False


# This optional report is constructed after private SQLite reads. Keep the
# import-original Python constructor/field hooks and False-only authority
# properties pinned across reentrant row hydration and hashing callbacks.
_REPORT_TYPE = MemoryGenerationReview
_ORIGINAL_REPORT_INIT = vars(_REPORT_TYPE)["__init__"]
_REPORT_FIELDS = (
    "memory_id", "event_count", "generation_count", "live_revision",
    "expected_revision", "revision_reuse_possible", "retained_history_sha256",
)
_ORIGINAL_REPORT_FIELDS = tuple(
    vars(_REPORT_TYPE)[name] for name in _REPORT_FIELDS
)
_REPORT_HOOKS = ("__new__", "__getattribute__", "__getattr__")
_ORIGINAL_REPORT_HOOKS = tuple(
    vars(_REPORT_TYPE).get(name) for name in _REPORT_HOOKS
)
_ORIGINAL_REPORT_DENIALS = tuple(
    vars(_REPORT_TYPE)[name] for name in _FLAGS
)


def _strict_utf8_identity(value: object, max_bytes: int) -> bool:
    """Bound optional read-only generation identities before private row access."""
    if type(value) is not str or not value.strip() or len(value) > max_bytes:
        return False
    try:
        return len(value.encode("utf-8", errors="strict")) <= max_bytes
    except UnicodeError:
        return False


_ORIGINAL_STRICT_IDENTITY = _strict_utf8_identity


def _require_original_report() -> None:
    if (
        MemoryGenerationReview is not _REPORT_TYPE
        or _strict_utf8_identity is not _ORIGINAL_STRICT_IDENTITY
        or vars(_REPORT_TYPE).get("__init__") is not _ORIGINAL_REPORT_INIT
        or any(
            vars(_REPORT_TYPE).get(name) is not original
            for name, original in zip(
                _REPORT_FIELDS, _ORIGINAL_REPORT_FIELDS, strict=True,
            )
        )
        or any(
            vars(_REPORT_TYPE).get(name) is not original
            for name, original in zip(
                _REPORT_HOOKS, _ORIGINAL_REPORT_HOOKS, strict=True,
            )
        )
        or any(
            vars(_REPORT_TYPE).get(name) is not original
            for name, original in zip(
                _FLAGS, _ORIGINAL_REPORT_DENIALS, strict=True,
            )
        )
    ):
        raise MemoryGenerationReviewRejected(
            "Memory generation report constructor or authority changed"
        )


def review_memory_revision_reuse(
    store: SQLiteMemoryStore,
    scope: MemoryScope,
    source_id: str,
    *,
    expected_revision: int,
) -> MemoryGenerationReview:
    """Observe exact saved event lifetimes in a single bounded read snapshot.

    A true revision_reuse_possible means the caller's numeric CAS revision
    alone cannot prove which lifetime it originally observed; even False
    does not grant write authority, trusted clock, consent or concurrency lock.
    """
    if (
        type(store) is not SQLiteMemoryStore
        or type(scope) is not MemoryScope
        or type(source_id) is not str
        or not source_id.strip()
        or len(source_id) > 512
        or type(expected_revision) is not int
        or not 0 <= expected_revision <= SQLITE_INT_MAX
    ):
        raise MemoryGenerationReviewRejected("exact bounded Memory generation inputs required")
    _require_original_report()
    # The frozen Memory v1 scope is character-bounded, not byte-bounded.
    # This optional reviewer must reject reflected malformed/surrogate labels
    # before deterministic ID hashing or any private SQLite access.
    if (
        not _strict_utf8_identity(scope.owner_id, 256)
        or not _strict_utf8_identity(scope.namespace, 256)
        or not _strict_utf8_identity(source_id, 512)
    ):
        raise MemoryGenerationReviewRejected(
            "generation review requires exact bounded UTF-8 scope and source"
        )
    # Preserve the FIRST caller-visible scope/path identities. Computing the
    # deterministic ID may call a reentrant test hash; sampling the epoch only
    # afterwards would silently adopt a substituted scope or SQLite source.
    owner, namespace = scope.owner_id, scope.namespace
    path = store.path
    original = (scope, owner, namespace, source_id, path)

    def stable() -> None:
        _require_original_report()
        if (
            type(store) is not SQLiteMemoryStore
            or type(scope) is not MemoryScope
            or store.path is not path
            or scope.owner_id is not original[1]
            or scope.namespace is not original[2]
            or source_id is not original[3]
        ):
            raise MemoryGenerationReviewRejected("generation source changed during review")

    # Recheck immediately after the first identity-hash boundary and before
    # opening private Memory. An equal-valued new string/Path is still a new
    # input epoch and must not be silently accepted.
    stable()
    memory_id = deterministic_memory_id(scope, source_id)
    stable()
    try:
        stable()
        with closing(store._connect_readonly()) as conn:
            stable()
            conn.execute("BEGIN")
            stable()
            try:
                _validate_v1_schema(conn)
                stable()
                # A valid-looking per-memory lifetime cannot prove that the
                # surrounding global v1 event append sequence is intact.
                # Reject gaps even when they belong to another owner or the
                # requested source has never existed. This is local
                # corruption detection, not authenticated log provenance.
                count, first, last = conn.execute(
                    "SELECT COUNT(*),MIN(event_id),MAX(event_id) FROM memory_events"
                ).fetchone()
                # sqlite_sequence.name is not UNIQUE. Refuse a second forged
                # marker even if the first marker matches the live event tip.
                sequences = conn.execute(
                    "SELECT seq FROM sqlite_sequence WHERE name='memory_events'"
                ).fetchall()
                stable()
                if (
                    type(count) is not int or count < 0
                    or count == 0 and (
                        first is not None or last is not None or sequences
                    )
                    or count > 0 and (
                        type(first) is not int or first != 1
                        or type(last) is not int or last != count
                        or last > SQLITE_INT_MAX
                        or len(sequences) != 1
                        or type(sequences[0][0]) is not int
                        or sequences[0][0] != last
                    )
                ):
                    raise MemoryGenerationReviewRejected(
                        "Memory generation global event high-water mismatch"
                    )
                row = conn.execute(
                    "SELECT * FROM memories WHERE memory_id=?",
                    (memory_id,),
                ).fetchone()
                stable()
                record = None if row is None else _record(row)
                stable()
                if record is not None and (
                    record.scope.owner_id != owner
                    or record.scope.namespace != namespace
                    or record.source_id != source_id
                    or record.memory_id != memory_id
                ):
                    raise MemoryGenerationReviewRejected(
                        "Memory row identity inconsistent with reviewed generation"
                    )
                events = conn.execute(
                    "SELECT event_id,owner_id,namespace,operation,revision,occurred_at_ms "
                    "FROM memory_events WHERE memory_id=? ORDER BY event_id LIMIT ?",
                    (memory_id, _MAX_EVENTS + 1),
                ).fetchall()
                stable()
                if len(events) > _MAX_EVENTS:
                    raise MemoryGenerationReviewRejected(
                        "Memory generation history exceeds bounded scan"
                    )
                active = False
                revision = 0
                generations = 0
                created_at = None
                updated_at = None
                previous_id = 0
                seen: list[tuple[int, str, int, int]] = []
                for event_id, event_owner, event_namespace, operation, rev, at in events:
                    stable()
                    if (
                        type(event_id) is not int
                        or event_id <= previous_id
                        or type(event_owner) is not str
                        or type(event_namespace) is not str
                        or (event_owner, event_namespace) != (owner, namespace)
                        or type(operation) is not str
                        or type(rev) is not int
                        or type(at) is not int
                        or not 0 <= at <= SQLITE_INT_MAX
                    ):
                        raise MemoryGenerationReviewRejected(
                            "Memory generation event identity invalid"
                        )
                    # A row-aligned final update can conceal an earlier
                    # backdated event. Keep restart diagnostics consistent
                    # with generation_fenced_cas._snapshot's clock floor.
                    if updated_at is not None and at < updated_at:
                        raise MemoryGenerationReviewRejected(
                            "Memory generation event clock regressed"
                        )
                    if operation == "create":
                        if active or rev != 1:
                            raise MemoryGenerationReviewRejected(
                                "Memory generation create/revision invalid"
                            )
                        active = True
                        revision = 1
                        generations += 1
                        created_at = at
                    elif operation == "update":
                        if not active or rev != revision + 1:
                            raise MemoryGenerationReviewRejected(
                                "Memory generation update sequence invalid"
                            )
                        revision = rev
                    elif operation in ("delete", "expire"):
                        if not active or rev != revision:
                            raise MemoryGenerationReviewRejected(
                                "Memory generation terminal event invalid"
                            )
                        active = False
                    else:
                        raise MemoryGenerationReviewRejected(
                            "Memory generation operation invalid"
                        )
                    previous_id = event_id
                    updated_at = at
                    seen.append((event_id, operation, rev, at))
                if (
                    active != (record is not None)
                    or record is not None and (
                        revision != record.revision
                        or created_at != record.created_at_ms
                        or updated_at != record.updated_at_ms
                    )
                ):
                    raise MemoryGenerationReviewRejected(
                        "Memory generation row/event lineage mismatch"
                    )
                conn.commit()
            except BaseException:
                conn.rollback()
                raise
    except sqlite3.Error as exc:
        raise MemoryGenerationReviewRejected("Memory generation database unavailable") from exc

    stable()
    fingerprint = hashlib.sha256(
        _DOMAIN + json.dumps(
            (memory_id, owner, namespace, tuple(seen)),
            separators=(",", ":"), ensure_ascii=True,
        ).encode("ascii")
    ).hexdigest()
    live = None if record is None else record.revision
    _require_original_report()
    result = _REPORT_TYPE(
        memory_id, len(seen), generations, live, expected_revision,
        generations > 1 and live == expected_revision, fingerprint,
    )
    expected_fields = (
        memory_id, len(seen), generations, live, expected_revision,
        generations > 1 and live == expected_revision, fingerprint,
    )

    def stable_result() -> None:
        _require_original_report()
        if (
            type(result) is not _REPORT_TYPE
            or any(
                current is not original
                for current, original in zip(
                    (result.memory_id, result.event_count,
                     result.generation_count, result.live_revision,
                     result.expected_revision, result.revision_reuse_possible,
                     result.retained_history_sha256),
                    expected_fields, strict=True,
                )
            )
        ):
            raise MemoryGenerationReviewRejected("Memory generation report changed")

    stable_result()
    for flag in _FLAGS:
        if getattr(result, flag) is not False:
            raise MemoryGenerationReviewRejected("Memory generation report gained authority")
        stable_result()
        stable()
    stable_result()
    return result
