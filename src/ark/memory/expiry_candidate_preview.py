"""Read-only, content-free preview of Memory v1 expiry candidates.

This diagnostic observes bounded rows in one SQLite read transaction and a
caller-supplied time. It never calls purge_expired, deletes, discloses content,
authenticates a clock/owner, or grants permission to erase anything.
"""

from __future__ import annotations

import hashlib
import json
import sqlite3
from contextlib import closing
from dataclasses import dataclass
from pathlib import Path

from .contracts import MemorySchemaError, MemoryScope
from .sqlite_store import SQLiteMemoryStore, _record, _validate_v1_schema

_DOMAIN = b"ARK-read-only-memory-expiry-preview-v1\0"
_MAX_ROWS = 1_000
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
_STORE_TYPE = SQLiteMemoryStore
_SCOPE_TYPE = MemoryScope


def _hash(tag: str, payload: object) -> str:
    encoded = json.dumps(
        payload, sort_keys=True, ensure_ascii=True,
        separators=(",", ":"), allow_nan=False,
    ).encode("ascii")
    return hashlib.sha256(_DOMAIN + tag.encode("ascii") + b"\0" + encoded).hexdigest()


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
    path = store.path
    owner, namespace = scope.owner_id, scope.namespace
    if not isinstance(path, Path):
        raise MemoryExpiryPreviewRejected("Memory source Path required")
    original = (owner, namespace)
    MemoryScope(owner, namespace)

    def stable() -> None:
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
                    if len(selected) < limit:
                        selected.append((
                            record.memory_id, record.revision, record.content_sha256,
                            record.updated_at_ms, record.expires_at_ms,
                        ))
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
    report = MemoryExpiryPreview(
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

    if not same_report() or any(
        getattr(report, flag) is not False for flag in _FLAGS
    ):
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
    for flag in _FLAGS:
        if getattr(report, flag) is not False:
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
    ):
        raise MemoryExpiryPreviewRejected("retained expiry page changed during review")
