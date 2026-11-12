"""One SQLite snapshot for bounded multi-namespace Memory expiry diagnostics.

Separate single-scope expiry previews can straddle concurrent commits. This
opt-in reviewer materializes all requested pages under ONE SQLite read
transaction, with one caller-supplied time and a shared event-scan budget.
No result permits deletion, implies owner consent, authenticates the clock,
or proves an independently retained historical inventory.
"""

from __future__ import annotations

import hashlib
import sqlite3
from contextlib import closing
from dataclasses import dataclass

from . import expiry_candidate_preview as preview_module
from . import expiry_cohort_review as cohort_module
from . import sqlite_store as store_module
from .contracts import MemoryScope
from .expiry_candidate_preview import MemoryExpiryPreview
from .expiry_cohort_review import MemoryExpiryCohort
from .sqlite_store import SQLiteMemoryStore

_MAX_SCOPES = 16
_MAX_ROWS_PER_SCOPE = 100
_MAX_TOTAL_ROWS = 1_616  # Include one overflow row for every scope.
_MAX_EVENT_SCAN = 40_000
_MAX_TIME = (1 << 63) - 1
_DOMAIN = b"ARK-coherent-expiry-snapshot-v1\0"

_ORIGINAL_HELPERS = (
    preview_module._assert_original_authority,
    preview_module._all_non_authorizing,
    preview_module._hash,
    preview_module._check_due_event_chain,
    preview_module._check_global_event_highwater,
    store_module._record,
    store_module._validate_v1_schema,
    cohort_module.aggregate_memory_expiry_cohort,
    hashlib.sha256,
)
_ORIGINAL_BOUNDS = (_MAX_SCOPES, _MAX_ROWS_PER_SCOPE, _MAX_TOTAL_ROWS,
                    _MAX_EVENT_SCAN, _MAX_TIME, _DOMAIN)


class CoherentExpirySnapshotRejected(ValueError):
    """The coherent content-free expiry read is not safe to publish."""


@dataclass(frozen=True, slots=True)
class CoherentExpirySnapshot:
    read_at_ms: int
    pages: tuple[MemoryExpiryPreview, ...]
    cohort: MemoryExpiryCohort
    snapshot_sha256: str

    @property
    def automatic_purge_authorized(self) -> bool:
        return False

    @property
    def trusted_clock_verified(self) -> bool:
        return False

    @property
    def owner_consent_authenticated(self) -> bool:
        return False

    @property
    def independent_historical_custody_proven(self) -> bool:
        return False

    @property
    def cross_store_atomicity_proven(self) -> bool:
        return False


_RESULT = CoherentExpirySnapshot
_RESULT_NAMES = (
    "read_at_ms", "pages", "cohort", "snapshot_sha256", "__init__",
    "__new__", "__getattribute__", "__getattr__",
    "automatic_purge_authorized", "trusted_clock_verified",
    "owner_consent_authenticated", "independent_historical_custody_proven",
    "cross_store_atomicity_proven",
)
_ORIGINAL_RESULT = tuple(vars(_RESULT).get(name) for name in _RESULT_NAMES)


def _protocol() -> None:
    now = (
        preview_module._assert_original_authority,
        preview_module._all_non_authorizing,
        preview_module._hash,
        preview_module._check_due_event_chain,
        preview_module._check_global_event_highwater,
        store_module._record,
        store_module._validate_v1_schema,
        cohort_module.aggregate_memory_expiry_cohort,
        hashlib.sha256,
    )
    if (
        any(current is not original for current, original in zip(
            now, _ORIGINAL_HELPERS, strict=True,
        ))
        or any(type(value) is not int for value in (
            _MAX_SCOPES, _MAX_ROWS_PER_SCOPE, _MAX_TOTAL_ROWS,
            _MAX_EVENT_SCAN, _MAX_TIME,
        ))
        or (_MAX_SCOPES, _MAX_ROWS_PER_SCOPE, _MAX_TOTAL_ROWS,
            _MAX_EVENT_SCAN, _MAX_TIME, _DOMAIN) != _ORIGINAL_BOUNDS
        or CoherentExpirySnapshot is not _RESULT
        or any(vars(_RESULT).get(name) is not old for name, old in zip(
            _RESULT_NAMES, _ORIGINAL_RESULT, strict=True,
        ))
    ):
        raise CoherentExpirySnapshotRejected("coherent expiry protocol changed")
    preview_module._assert_original_authority()
    cohort_module._protocol()


def review_coherent_expiry_snapshot(
    store: SQLiteMemoryStore,
    scopes: tuple[MemoryScope, ...],
    *,
    now_ms: int,
    limit: int = 100,
) -> CoherentExpirySnapshot:
    """Return content-free per-scope pages from ONE pinned read transaction.

    Scopes must belong to one exact owner. Returned pages are sorted by
    scope hash because the existing cohort verifier has a canonical order.
    The caller's inventory is an assertion, NOT independent custody.
    """
    _protocol()
    if (
        type(store) is not SQLiteMemoryStore
        or type(scopes) is not tuple
        or not 1 <= len(scopes) <= _MAX_SCOPES
        or any(type(scope) is not MemoryScope for scope in scopes)
        or type(now_ms) is not int or not 0 <= now_ms <= _MAX_TIME
        or type(limit) is not int or not 1 <= limit <= _MAX_ROWS_PER_SCOPE
    ):
        raise CoherentExpirySnapshotRejected("inexact or unbounded expiry request")
    original_path = store.path
    original_scopes = tuple(
        (scope, scope.owner_id, scope.namespace) for scope in scopes
    )
    if (
        any(type(owner) is not str or type(namespace) is not str
            for _, owner, namespace in original_scopes)
        or len({(owner, namespace) for _, owner, namespace in original_scopes})
        != len(original_scopes)
        or len({owner for _, owner, _ in original_scopes}) != 1
    ):
        raise CoherentExpirySnapshotRejected("mixed or duplicate expiry owners/scopes")
    try:
        for _, owner, namespace in original_scopes:
            MemoryScope(owner, namespace)
            owner.encode("utf-8", "strict")
            namespace.encode("utf-8", "strict")
    except (TypeError, ValueError, UnicodeError) as exc:
        raise CoherentExpirySnapshotRejected("invalid expiry scope") from exc

    def stable() -> None:
        _protocol()
        if (
            type(store) is not SQLiteMemoryStore
            or store.path is not original_path
            or type(scopes) is not tuple
            or len(scopes) != len(original_scopes)
            or any(
                type(scope) is not MemoryScope
                or scope is not original
                or scope.owner_id is not owner
                or scope.namespace is not namespace
                for scope, (original, owner, namespace) in zip(
                    scopes, original_scopes, strict=True,
                )
            )
        ):
            raise CoherentExpirySnapshotRejected("expiry source changed during read")

    stable()
    pages = []
    total_rows = 0
    remaining_events = _MAX_EVENT_SCAN
    try:
        with closing(store._connect_readonly()) as conn:
            conn.execute("BEGIN")
            try:
                stable()
                store_module._validate_v1_schema(conn)
                preview_module._check_global_event_highwater(conn)
                for _, owner, namespace in original_scopes:
                    stable()
                    rows = conn.execute(
                        "SELECT * FROM memories WHERE owner_id=? AND namespace=? "
                        "AND expires_at_ms IS NOT NULL AND expires_at_ms<=? "
                        "ORDER BY memory_id LIMIT ?",
                        (owner, namespace, now_ms, limit + 1),
                    ).fetchall()
                    total_rows += len(rows)
                    if total_rows > _MAX_TOTAL_ROWS:
                        raise CoherentExpirySnapshotRejected(
                            "coherent expiry row budget exhausted"
                        )
                    selected = []
                    for row in rows:
                        stable()
                        record = store_module._record(row)
                        stable()
                        if (
                            type(record.scope) is not MemoryScope
                            or (record.scope.owner_id, record.scope.namespace)
                            != (owner, namespace)
                            or record.expires_at_ms is None
                            or record.expires_at_ms > now_ms
                        ):
                            raise CoherentExpirySnapshotRejected(
                                "expiry candidate scope/time mismatch"
                            )
                        remaining_events -= preview_module._check_due_event_chain(
                            conn, record, (owner, namespace), remaining_events,
                        )
                        stable()
                        if len(selected) < limit:
                            selected.append((
                                record.memory_id, record.revision,
                                record.content_sha256, record.updated_at_ms,
                                record.expires_at_ms,
                            ))
                    scope_hash = preview_module._hash("scope", (owner, namespace))
                    candidate_hash = preview_module._hash(
                        "rows", tuple(selected),
                    )
                    more = len(rows) > limit
                    digest = preview_module._hash(
                        "preview", (scope_hash, now_ms, limit,
                                    len(selected), more, candidate_hash),
                    )
                    stable()
                    page = MemoryExpiryPreview(
                        scope_hash, now_ms, len(selected),
                        more, candidate_hash, digest,
                    )
                    if not preview_module._all_non_authorizing(page):
                        raise CoherentExpirySnapshotRejected(
                            "expiry page acquired authority"
                        )
                    stable()
                    pages.append(page)
                preview_module._check_global_event_highwater(conn)
                stable()
                conn.commit()
            except BaseException:
                conn.rollback()
                raise
    except sqlite3.Error as exc:
        raise CoherentExpirySnapshotRejected(
            "coherent expiry SQLite read failed"
        ) from exc

    stable()
    sorted_pages = tuple(sorted(pages, key=lambda page: page.scope_sha256))
    inventory = tuple(page.scope_sha256 for page in sorted_pages)
    try:
        cohort = cohort_module.aggregate_memory_expiry_cohort(
            independently_expected_scope_hashes=inventory,
            previews=sorted_pages,
            asserted_now_ms=now_ms,
        )
    except cohort_module.MemoryExpiryCohortRejected as exc:
        raise CoherentExpirySnapshotRejected("expiry cohort rejected") from exc
    stable()
    if cohort.deletion_authorized is not False:
        raise CoherentExpirySnapshotRejected("expiry cohort gained deletion authority")
    digest = preview_module._hash(
        "coherent", (_DOMAIN.decode("ascii"), now_ms, limit,
                     cohort.cohort_sha256, inventory),
    )
    stable()
    result = _RESULT(now_ms, sorted_pages, cohort, digest)
    if (
        type(result) is not _RESULT
        or result.pages is not sorted_pages
        or result.cohort is not cohort
        or result.snapshot_sha256 != digest
        or any(getattr(result, flag) is not False for flag in (
            "automatic_purge_authorized", "trusted_clock_verified",
            "owner_consent_authenticated", "independent_historical_custody_proven",
            "cross_store_atomicity_proven",
        ))
    ):
        raise CoherentExpirySnapshotRejected("expiry snapshot acquired authority")
    stable()
    return result
