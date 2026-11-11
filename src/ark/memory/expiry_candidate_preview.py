"""Read-only, content-free preview of Memory v1 expiry candidates.

This diagnostic observes bounded rows in one SQLite read transaction and a
caller-supplied time. It never calls purge_expired, deletes, discloses content,
authenticates a clock/owner, or grants permission to erase anything.
"""

from __future__ import annotations

import hashlib
import inspect
import json
import sqlite3
from contextlib import closing
from dataclasses import dataclass
from pathlib import Path

from .contracts import MemoryRecord, MemorySchemaError, MemoryScope
from .sqlite_store import SQLiteMemoryStore, _record, _validate_v1_schema

_DOMAIN = b"ARK-read-only-memory-expiry-preview-v1\0"
_MAX_ROWS = 1_000
_MAX_EVENT_SCAN = 40_000  # Aggregate cap across all returned and overflow rows.
_MAX_TIME = (1 << 63) - 1
_FLAGS = (
    "deletion_authorized", "physical_erasure_proven",
    "owner_consent_authenticated", "trusted_clock_verified",
    "external_disclosure_authorized",
)


class MemoryExpiryPreviewRejected(MemorySchemaError):
    """Local expiry candidate snapshot could not be safely reviewed."""


@dataclass(frozen=True, slots=True)
class MemoryExpiryPreview:
    scope_sha256: str
    read_at_ms: int
    candidate_count: int
    has_more: bool
    candidate_sha256: str
    preview_sha256: str

    @property
    def deletion_authorized(self) -> bool:
        return False

    @property
    def physical_erasure_proven(self) -> bool:
        return False

    @property
    def owner_consent_authenticated(self) -> bool:
        return False

    @property
    def trusted_clock_verified(self) -> bool:
        return False

    @property
    def external_disclosure_authorized(self) -> bool:
        return False


_RECEIPT_TYPE = MemoryExpiryPreview
_ORIGINAL_RECEIPT_INIT = vars(_RECEIPT_TYPE)["__init__"]
_RECEIPT_FIELDS = (
    "scope_sha256", "read_at_ms", "candidate_count", "has_more",
    "candidate_sha256", "preview_sha256",
)
_ORIGINAL_RECEIPT_FIELDS = tuple(
    vars(_RECEIPT_TYPE)[name] for name in _RECEIPT_FIELDS
)
_RECEIPT_HOOKS = ("__new__", "__getattr__", "__getattribute__")
_ORIGINAL_RECEIPT_HOOKS = tuple(
    vars(_RECEIPT_TYPE).get(name) for name in _RECEIPT_HOOKS
)
_STORE_TYPE = SQLiteMemoryStore
_SCOPE_TYPE = MemoryScope
# A digest of private candidate metadata is not meaningful if its codec
# or domain can be rebound before the read-only review begins.
_ORIGINAL_HASHLIB = hashlib
_ORIGINAL_JSON = json
_ORIGINAL_SHA256 = hashlib.sha256
_ORIGINAL_DUMPS = json.dumps
_ORIGINAL_DOMAIN = _DOMAIN
_ORIGINAL_BOUNDS = (_MAX_ROWS, _MAX_EVENT_SCAN, _MAX_TIME)

_AUTHORITY_DESCRIPTORS = tuple(
    getattr(_RECEIPT_TYPE, flag) for flag in _FLAGS
)


def _assert_original_authority() -> None:
    """Deny substituted authority callbacks before touching Memory SQLite."""
    if (
        hashlib is not _ORIGINAL_HASHLIB
        or json is not _ORIGINAL_JSON
        or hashlib.sha256 is not _ORIGINAL_SHA256
        or json.dumps is not _ORIGINAL_DUMPS
        or _DOMAIN is not _ORIGINAL_DOMAIN
        or any(
            type(value) is not int
            for value in (_MAX_ROWS, _MAX_EVENT_SCAN, _MAX_TIME)
        )
        or (_MAX_ROWS, _MAX_EVENT_SCAN, _MAX_TIME) != _ORIGINAL_BOUNDS
        or _check_global_event_highwater is not _ORIGINAL_GLOBAL_HIGHWATER_CHECK
        or _check_due_event_chain is not _ORIGINAL_DUE_CHAIN_CHECK
    ):
        raise MemoryExpiryPreviewRejected("expiry digest protocol changed")
    if (
        MemoryExpiryPreview is not _RECEIPT_TYPE
        or vars(_RECEIPT_TYPE).get("__init__") is not _ORIGINAL_RECEIPT_INIT
        or any(
            vars(_RECEIPT_TYPE).get(name) is not original
            for name, original in zip(
                _RECEIPT_FIELDS, _ORIGINAL_RECEIPT_FIELDS, strict=True,
            )
        )
        or any(
            vars(_RECEIPT_TYPE).get(name) is not original
            for name, original in zip(
                _RECEIPT_HOOKS, _ORIGINAL_RECEIPT_HOOKS, strict=True,
            )
        )
        or any(
            # getattr() on a class can itself execute a hostile __get__.
            # Identity inspection must never run a substituted descriptor.
            vars(_RECEIPT_TYPE).get(flag) is not original
            for flag, original in zip(
                _FLAGS, _AUTHORITY_DESCRIPTORS, strict=True,
            )
        )
    ):
        raise MemoryExpiryPreviewRejected("expiry authority descriptor changed")


def _all_non_authorizing(report: MemoryExpiryPreview) -> bool:
    """Check exact False flags and original descriptors after each callback."""
    _assert_original_authority()
    if type(report) is not _RECEIPT_TYPE:
        return False
    for flag, original in zip(_FLAGS, _AUTHORITY_DESCRIPTORS, strict=True):
        _assert_original_authority()
        if inspect.getattr_static(report, flag, None) is not original:
            return False
        if getattr(report, flag) is not False:
            return False
        _assert_original_authority()
    return True



def _hash(tag: str, payload: object) -> str:
    encoded = json.dumps(
        payload, sort_keys=True, ensure_ascii=True,
        separators=(",", ":"), allow_nan=False,
    ).encode("ascii")
    return hashlib.sha256(_DOMAIN + tag.encode("ascii") + b"\0" + encoded).hexdigest()



def _check_global_event_highwater(conn: sqlite3.Connection) -> None:
    """Refuse an incomplete append log even when due rows look consistent.

    Scope-filtered candidate history alone cannot detect a missing event
    belonging to another owner, an already deleted row, or an empty due page.
    SQLite AUTOINCREMENT high-water is local consistency, not provenance.
    """
    count, first, last = conn.execute(
        "SELECT COUNT(*),MIN(event_id),MAX(event_id) FROM memory_events"
    ).fetchone()
    # sqlite_sequence.name is NOT UNIQUE. A forged duplicate can hide behind
    # fetchone() even when SQLite quick_check reports a healthy database.
    # Read all high-water markers inside the same candidate snapshot.
    seq_rows = conn.execute(
        "SELECT seq FROM sqlite_sequence WHERE name='memory_events'"
    ).fetchall()
    if (
        type(count) is not int or count < 0
        or (
            count == 0
            and (first is not None or last is not None or seq_rows)
        )
        or (
            count > 0
            and (
                type(first) is not int or first != 1
                or type(last) is not int or last != count
                or last > _MAX_TIME
                or len(seq_rows) != 1
                or type(seq_rows[0][0]) is not int
                or seq_rows[0][0] != last
            )
        )
    ):
        raise MemoryExpiryPreviewRejected(
            "expiry preview global event high-water mismatch"
        )



_ORIGINAL_GLOBAL_HIGHWATER_CHECK = _check_global_event_highwater


def _check_due_event_chain(
    conn: sqlite3.Connection,
    record: MemoryRecord,
    scope: tuple[str, str],
    remaining: int,
) -> int:
    """Reconcile the complete persisted lifecycle in the *existing* read snapshot.

    Rev 1 may legitimately recur after delete/expire and recreation. A live
    cycle must start with create, advance revisions one step per update, and
    end at precisely the selected row's create/update timestamp. A bounded
    scan fails closed if history cannot be checked without exhausting budget.
    This is integrity checking, never authenticated authorship or erase consent.
    """
    if remaining <= 0:
        raise MemoryExpiryPreviewRejected("expiry event scan budget exceeded")
    events = conn.execute(
        "SELECT event_id,owner_id,namespace,operation,revision,occurred_at_ms "
        "FROM memory_events WHERE memory_id=? ORDER BY event_id LIMIT ?",
        (record.memory_id, remaining + 1),
    ).fetchall()
    if len(events) > remaining:
        raise MemoryExpiryPreviewRejected("expiry event scan budget exceeded")
    active = False
    revision = 0
    created_at = None
    last_at = None
    previous_event_id = 0
    for event_id, owner, namespace, operation, event_revision, at in events:
        if (
            type(event_id) is not int
            or event_id <= previous_event_id
            or type(owner) is not str
            or type(namespace) is not str
            or (owner, namespace) != scope
            or type(operation) is not str
            or type(event_revision) is not int
            or type(at) is not int
            or not 0 <= at <= _MAX_TIME
        ):
            raise MemoryExpiryPreviewRejected(
                "expiry candidate lacks matching live Memory event"
            )
        # A row can be coherent with a forged latest event while its earlier
        # per-memory timestamps move backward. Reject the entire lifecycle,
        # including delete/recreate epochs, before naming an expiry candidate.
        if last_at is not None and at < last_at:
            raise MemoryExpiryPreviewRejected(
                "expiry candidate event clock regressed"
            )
        previous_event_id = event_id
        if operation == "create":
            if active or event_revision != 1:
                raise MemoryExpiryPreviewRejected(
                    "expiry candidate lacks matching live Memory event"
                )
            active, revision, created_at = True, 1, at
        elif operation == "update":
            if not active or event_revision != revision + 1:
                raise MemoryExpiryPreviewRejected(
                    "expiry candidate lacks matching live Memory event"
                )
            revision = event_revision
        elif operation in ("delete", "expire"):
            if not active or event_revision != revision:
                raise MemoryExpiryPreviewRejected(
                    "expiry candidate lacks matching live Memory event"
                )
            active = False
        else:
            raise MemoryExpiryPreviewRejected(
                "expiry candidate lacks matching live Memory event"
            )
        last_at = at
    if (
        not active
        or revision != record.revision
        or created_at != record.created_at_ms
        or last_at != record.updated_at_ms
    ):
        raise MemoryExpiryPreviewRejected(
            "expiry candidate lacks matching live Memory event"
        )
    return len(events)


_ORIGINAL_DUE_CHAIN_CHECK = _check_due_event_chain


def review_memory_expiry_candidates(
    store: SQLiteMemoryStore,
    scope: MemoryScope,
    *,
    now_ms: int,
    limit: int = 100,
) -> MemoryExpiryPreview:
    """Preview up to limit due rows; has_more forbids interpreting a page as all."""
    if (
        type(store) is not _STORE_TYPE
        or type(scope) is not _SCOPE_TYPE
        or type(now_ms) is not int
        or not 0 <= now_ms <= _MAX_TIME
        or type(limit) is not int
        or not 1 <= limit <= _MAX_ROWS
    ):
        raise MemoryExpiryPreviewRejected("exact bounded expiry preview inputs required")
    _assert_original_authority()
    path = store.path
    owner, namespace = scope.owner_id, scope.namespace
    if not isinstance(path, Path):
        raise MemoryExpiryPreviewRejected("Memory source Path required")
    original = (owner, namespace)
    MemoryScope(owner, namespace)

    def stable() -> None:
        _assert_original_authority()
        if (
            type(store) is not _STORE_TYPE
            or store.path is not path
            or type(scope) is not _SCOPE_TYPE
            or scope.owner_id is not original[0]
            or scope.namespace is not original[1]
        ):
            raise MemoryExpiryPreviewRejected("Memory expiry preview inputs changed")

    stable()
    selected: list[tuple[str, int, str, int, int]] = []
    remaining_events = _MAX_EVENT_SCAN
    try:
        with closing(store._connect_readonly()) as conn:
            stable()
            conn.execute("BEGIN")
            stable()
            try:
                _validate_v1_schema(conn)
                stable()
                rows = conn.execute(
                    """SELECT * FROM memories WHERE owner_id=? AND namespace=?
                       AND expires_at_ms IS NOT NULL AND expires_at_ms<=?
                       ORDER BY memory_id LIMIT ?""",
                    (owner, namespace, now_ms, limit + 1),
                ).fetchall()
                stable()
                if len(rows) > limit + 1:
                    raise MemoryExpiryPreviewRejected("expiry page budget exceeded")
                for row in rows:
                    stable()
                    record = _record(row)
                    stable()
                    if (
                        type(record.scope) is not _SCOPE_TYPE
                        or (record.scope.owner_id, record.scope.namespace) != original
                        or record.expires_at_ms is None
                        or record.expires_at_ms > now_ms
                    ):
                        raise MemoryExpiryPreviewRejected("expiry candidate scope or time drift")
                    # Validate the entire row lifecycle, including previous
                    # delete/recreate cycles, using THIS SQLite snapshot. The
                    # limit+1 overflow row must pass the same review.
                    remaining_events -= _check_due_event_chain(
                        conn, record, original, remaining_events,
                    )
                    stable()
                    if len(selected) < limit:
                        selected.append((
                            record.memory_id, record.revision, record.content_sha256,
                            record.updated_at_ms, record.expires_at_ms,
                        ))
                stable()
                # The whole append high-water must be complete in this same
                # pinned read snapshot, including if there are no due rows.
                _check_global_event_highwater(conn)
                stable()
                conn.commit()
            except BaseException:
                conn.rollback()
                raise
    except sqlite3.Error as exc:
        raise MemoryExpiryPreviewRejected("expiry database cannot be inspected") from exc
    stable()
    scope_hash = _hash("scope", original)
    candidate_hash = _hash("rows", tuple(selected))
    more = len(rows) > limit
    fingerprint = _hash(
        "preview", (scope_hash, now_ms, limit, len(selected), more, candidate_hash),
    )
    # A substituted dataclass constructor can execute untrusted code before
    # the existing postconstruction deny-only checks. Reject such drift
    # before constructing any read-only expiry preview receipt.
    _assert_original_authority()
    report = _RECEIPT_TYPE(
        scope_hash, now_ms, len(selected), more, candidate_hash, fingerprint,
    )
    stable()
    def same_report() -> bool:
        return (
            type(report) is _RECEIPT_TYPE
            and report.scope_sha256 is scope_hash
            and report.read_at_ms is now_ms
            and type(report.candidate_count) is int
            and report.candidate_count == len(selected)
            and type(report.has_more) is bool
            and report.has_more is more
            and report.candidate_sha256 is candidate_hash
            and report.preview_sha256 is fingerprint
        )

    if not same_report() or not _all_non_authorizing(report):
        raise MemoryExpiryPreviewRejected("expiry report gained authority or changed")
    # Authority getters are callbacks: a False result may conceal mutation
    # of the frozen receipt or original source scope.
    stable()
    if not same_report():
        raise MemoryExpiryPreviewRejected("expiry report changed after authority review")
    return report


def verify_memory_expiry_preview(
    report: MemoryExpiryPreview,
    store: SQLiteMemoryStore,
    scope: MemoryScope,
    *,
    now_ms: int,
    limit: int,
    retained_preview_sha256: str,
) -> None:
    """Re-read a bounded page; evidence is neither erasure nor permission.

    The retained digest is an independently supplied comparison value, not a
    clock, custody proof, consent, or authorization to run a later purge.
    """
    if (
        type(report) is not _RECEIPT_TYPE
        or type(retained_preview_sha256) is not str
        or len(retained_preview_sha256) != 64
        or any(c not in "0123456789abcdef" for c in retained_preview_sha256)
    ):
        raise MemoryExpiryPreviewRejected("exact retained expiry fingerprint required")
    _assert_original_authority()

    # The retained receipt has identity-bearing scalar carriers. Re-reading
    # a mutable SQLite page must not silently accept a value-equal replacement
    # of those carriers inside a reflected frozen dataclass.
    original_receipt_fields = (
        report.scope_sha256, report.read_at_ms, report.candidate_count,
        report.has_more, report.candidate_sha256, report.preview_sha256,
    )
    retained_scope, retained_time, count, more, rows_hash, preview_hash = (
        original_receipt_fields
    )
    # Reject malformed or clearly mismatched detached evidence before opening
    # private SQLite. A reflected frozen receipt can contain bool-as-int or an
    # executable equality carrier; compare only after exact-type validation.
    if (
        type(now_ms) is not int or not 0 <= now_ms <= _MAX_TIME
        or type(limit) is not int or not 1 <= limit <= _MAX_ROWS
        or type(retained_time) is not int or retained_time != now_ms
        or type(count) is not int or not 0 <= count <= limit
        or type(more) is not bool
        or any(
            type(value) is not str
            or len(value) != 64
            or any(c not in "0123456789abcdef" for c in value)
            for value in (retained_scope, rows_hash, preview_hash)
        )
        or preview_hash != retained_preview_sha256
    ):
        raise MemoryExpiryPreviewRejected("retained expiry preview mismatch")
    _assert_original_authority()
    source_path = store.path if type(store) is _STORE_TYPE else None
    owner = scope.owner_id if type(scope) is _SCOPE_TYPE else None
    namespace = scope.namespace if type(scope) is _SCOPE_TYPE else None

    def stable_sources() -> None:
        if (
            type(store) is not _STORE_TYPE
            or store.path is not source_path
            or type(scope) is not _SCOPE_TYPE
            or scope.owner_id is not owner
            or scope.namespace is not namespace
        ):
            raise MemoryExpiryPreviewRejected("retained expiry source changed")

    expected = review_memory_expiry_candidates(
        store, scope, now_ms=now_ms, limit=limit,
    )
    stable_sources()

    def exact_fields() -> bool:
        # Never trust a replaceable dataclass __eq__ or coercible booleans.
        return (
            type(report) is _RECEIPT_TYPE
            and all(
                current is original for current, original in zip(
                    (
                        report.scope_sha256, report.read_at_ms, report.candidate_count,
                        report.has_more, report.candidate_sha256, report.preview_sha256,
                    ),
                    original_receipt_fields, strict=True,
                )
            )
            and type(report.scope_sha256) is str
            and report.scope_sha256 == expected.scope_sha256
            and type(report.read_at_ms) is int
            and report.read_at_ms == expected.read_at_ms
            and type(report.candidate_count) is int
            and report.candidate_count == expected.candidate_count
            and type(report.has_more) is bool
            and report.has_more is expected.has_more
            and type(report.candidate_sha256) is str
            and report.candidate_sha256 == expected.candidate_sha256
            and type(report.preview_sha256) is str
            and report.preview_sha256 == expected.preview_sha256
            and report.preview_sha256 == retained_preview_sha256
        )

    if not exact_fields():
        raise MemoryExpiryPreviewRejected("retained expiry preview mismatch")
    if not _all_non_authorizing(report):
        raise MemoryExpiryPreviewRejected("retained expiry preview gained authority")
    # Even the final denial getter may mutate a frozen report, scope, or
    # SQLite page. Check those after all callbacks, and recompute the page
    # without granting a future TOCTOU-free deletion guarantee.
    stable_sources()
    if not exact_fields():
        raise MemoryExpiryPreviewRejected("retained expiry preview changed after denial")
    latest = review_memory_expiry_candidates(
        store, scope, now_ms=now_ms, limit=limit,
    )
    stable_sources()
    if (
        not exact_fields()
        or type(latest) is not _RECEIPT_TYPE
        or latest.preview_sha256 != expected.preview_sha256
        or not _all_non_authorizing(report)
        or not _all_non_authorizing(latest)
    ):
        raise MemoryExpiryPreviewRejected("retained expiry page changed during review")
    # An authority getter itself may mutate this retained receipt, or return
    # False only until the final SQLite scan. Recheck after those callbacks.
    stable_sources()
    if not exact_fields() or not _all_non_authorizing(report):
        raise MemoryExpiryPreviewRejected(
            "retained expiry report changed after final denial"
        )
    stable_sources()
    if not exact_fields():
        raise MemoryExpiryPreviewRejected("retained expiry report changed at return")
