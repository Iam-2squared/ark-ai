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
    if (
        type(report) is not _RECEIPT_TYPE
        or report.scope_sha256 is not scope_hash
        or report.read_at_ms is not now_ms
        or type(report.candidate_count) is not int
        or report.candidate_count != len(selected)
        or type(report.has_more) is not bool
        or report.has_more is not more
        or report.candidate_sha256 is not candidate_hash
        or report.preview_sha256 is not fingerprint
        or any(getattr(report, flag) is not False for flag in _FLAGS)
    ):
        raise MemoryExpiryPreviewRejected("expiry report gained authority or changed")
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
    """Re-read an unchanged page; no permission to perform a future purge."""
    if (
        type(report) is not _RECEIPT_TYPE
        or type(retained_preview_sha256) is not str
        or len(retained_preview_sha256) != 64
        or any(c not in "0123456789abcdef" for c in retained_preview_sha256)
    ):
        raise MemoryExpiryPreviewRejected("exact retained expiry fingerprint required")
    expected = review_memory_expiry_candidates(
        store, scope, now_ms=now_ms, limit=limit,
    )
    if (
        type(report.scope_sha256) is not str
        or type(report.read_at_ms) is not int
        or type(report.candidate_count) is not int
        or type(report.has_more) is not bool
        or type(report.candidate_sha256) is not str
        or type(report.preview_sha256) is not str
        or report.preview_sha256 != retained_preview_sha256
        or report != expected
        or any(getattr(report, flag) is not False for flag in _FLAGS)
    ):
        raise MemoryExpiryPreviewRejected("retained expiry preview mismatch")
