"""Compare a retained coherent Memory expiry read with a fresh SQLite epoch.

The previous observation is caller-controlled and may be stale; this bridge
checks its digest, reopens the live database read-only and compares bounded
pages without exposing private content. No clock attestation or purge grant.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass

from . import coherent_expiry_snapshot_review as coherent
from . import expiry_restart_receipt_review as restart
from .contracts import MemoryScope
from .sqlite_store import SQLiteMemoryStore

_DOMAIN = b"ARK-coherent-expiry-restart-bridge-v1\0"
_ORIGINAL_COHERENT = coherent.review_coherent_expiry_snapshot
_ORIGINAL_COHERENT_GUARD = coherent._protocol
_ORIGINAL_RESTART = restart.review_memory_expiry_restart_receipt
_ORIGINAL_RESTART_GUARD = restart._protocol
_ORIGINAL_HASH = hashlib.sha256
_ORIGINAL_JSON = json.dumps
_ORIGINAL_DOMAIN = _DOMAIN


class CoherentExpiryRestartRejected(ValueError):
    """Retained and fresh Memory expiry epochs cannot be safely reconciled."""


@dataclass(frozen=True, slots=True)
class CoherentExpiryRestartReview:
    previous_snapshot_sha256: str
    observed_snapshot_sha256: str
    transition: str
    previous_candidates: int
    observed_candidates: int
    receipt_sha256: str

    @property
    def automatic_purge_authorized(self) -> bool:
        return False

    @property
    def trusted_clock_verified(self) -> bool:
        return False

    @property
    def independent_custody_verified(self) -> bool:
        return False

    @property
    def historical_completeness_proven(self) -> bool:
        return False

    @property
    def cross_epoch_atomicity_proven(self) -> bool:
        return False


_RESULT = CoherentExpiryRestartReview
_FIELDS = (
    "previous_snapshot_sha256", "observed_snapshot_sha256", "transition",
    "previous_candidates", "observed_candidates", "receipt_sha256",
    "automatic_purge_authorized", "trusted_clock_verified",
    "independent_custody_verified", "historical_completeness_proven",
    "cross_epoch_atomicity_proven", "__init__", "__new__",
    "__getattribute__", "__getattr__",
)
_ORIGINAL_FIELDS = tuple(vars(_RESULT).get(field) for field in _FIELDS)


def _protocol() -> None:
    if (
        coherent.review_coherent_expiry_snapshot is not _ORIGINAL_COHERENT
        or coherent._protocol is not _ORIGINAL_COHERENT_GUARD
        or restart.review_memory_expiry_restart_receipt is not _ORIGINAL_RESTART
        or restart._protocol is not _ORIGINAL_RESTART_GUARD
        or hashlib.sha256 is not _ORIGINAL_HASH
        or json.dumps is not _ORIGINAL_JSON
        or _DOMAIN is not _ORIGINAL_DOMAIN
        or CoherentExpiryRestartReview is not _RESULT
        or any(
            vars(_RESULT).get(field) is not original
            for field, original in zip(_FIELDS, _ORIGINAL_FIELDS, strict=True)
        )
    ):
        raise CoherentExpiryRestartRejected("coherent restart bridge protocol changed")
    _ORIGINAL_COHERENT_GUARD()
    _ORIGINAL_RESTART_GUARD()


def review_coherent_expiry_restart(
    store: SQLiteMemoryStore,
    scopes: tuple[MemoryScope, ...],
    retained: coherent.CoherentExpirySnapshot,
    *,
    now_ms: int,
    limit: int = 100,
) -> CoherentExpiryRestartReview:
    """Rebuild live pages in one SQLite epoch and compare retained prior pages.

    The independently expected scope hashes are asserted by the caller from
    the scope tuple; they are NOT independently authenticated historical data.
    The review is immediately stale if another writer commits afterward.
    """
    _protocol()
    if (
        type(store) is not SQLiteMemoryStore
        or type(scopes) is not tuple
        or not 1 <= len(scopes) <= coherent._MAX_SCOPES
        or any(type(scope) is not MemoryScope for scope in scopes)
        or type(retained) is not coherent.CoherentExpirySnapshot
        or type(now_ms) is not int
        or not 0 <= now_ms <= coherent._MAX_TIME
        or type(limit) is not int
        or not 1 <= limit <= coherent._MAX_ROWS_PER_SCOPE
    ):
        raise CoherentExpiryRestartRejected("inexact coherent restart inputs")
    # Exact bounded scope carriers and clock/limit were checked above BEFORE
    # reading even one owner/namespace property. An inexact scope proxy can
    # execute code on attribute access; it is never valid retained evidence.
    original_scopes = tuple((scope, scope.owner_id, scope.namespace) for scope in scopes)
    prior_epoch = (
        retained.read_at_ms, retained.pages, retained.cohort,
        retained.snapshot_sha256,
    )
    original_path = store.path
    # Reject malformed retained outer carriers BEFORE iteration/field access.
    # A reflected frozen `pages` slot can contain a hostile non-tuple iterator,
    # and a forged cohort may have executable attributes.  Neither is local
    # historical evidence, so do not invoke their callbacks.
    if (
        type(retained.pages) is not tuple
        or not 1 <= len(retained.pages) <= 16
        or any(
            type(page) is not coherent.preview_module.MemoryExpiryPreview
            for page in retained.pages
        )
        or type(retained.cohort) is not coherent.MemoryExpiryCohort
    ):
        raise CoherentExpiryRestartRejected("invalid retained snapshot carriers")
    # A frozen dataclass is not immutable under object.__setattr__.  The
    # retained page/cohort values must remain the same throughout the fresh
    # SQLite callback and the separate transition reviewer, otherwise a
    # post-commit diagnosis may combine two different historical assertions.
    page_epoch = tuple(
        (page, page.scope_sha256, page.read_at_ms, page.candidate_count,
         page.has_more, page.candidate_sha256, page.preview_sha256)
        for page in retained.pages
    )
    cohort_epoch = (
        retained.cohort, retained.cohort.scope_hashes,
        retained.cohort.asserted_now_ms, retained.cohort.candidate_count,
        retained.cohort.truncated_scopes, retained.cohort.cohort_sha256,
    )

    def stable() -> None:
        _protocol()
        if (
            store.path is not original_path
            or len(scopes) != len(original_scopes)
            or any(
                scope is not old or type(scope) is not MemoryScope
                or scope.owner_id is not owner or scope.namespace is not namespace
                for scope, (old, owner, namespace) in zip(
                    scopes, original_scopes, strict=True,
                )
            )
            or any(current is not old for current, old in zip(
                (retained.read_at_ms, retained.pages, retained.cohort,
                 retained.snapshot_sha256), prior_epoch, strict=True,
            ))
            or len(retained.pages) != len(page_epoch)
            or any(
                type(page) is not coherent.preview_module.MemoryExpiryPreview
                or page is not old
                or (
                    page.scope_sha256, page.read_at_ms, page.candidate_count,
                    page.has_more, page.candidate_sha256, page.preview_sha256,
                ) != (scope, read_at, count, more, candidate, digest)
                for page, (old, scope, read_at, count, more, candidate, digest)
                in zip(retained.pages, page_epoch, strict=True)
            )
            or type(retained.cohort) is not coherent.MemoryExpiryCohort
            or retained.cohort is not cohort_epoch[0]
            or (
                retained.cohort.scope_hashes, retained.cohort.asserted_now_ms,
                retained.cohort.candidate_count, retained.cohort.truncated_scopes,
                retained.cohort.cohort_sha256,
            ) != cohort_epoch[1:]
        ):
            raise CoherentExpiryRestartRejected("coherent restart inputs changed")

    stable()
    if (
        type(retained.read_at_ms) is not int
        or type(retained.pages) is not tuple
        or type(retained.cohort) is not coherent.MemoryExpiryCohort
        or type(retained.snapshot_sha256) is not str
        or not 0 <= retained.read_at_ms <= now_ms
    ):
        raise CoherentExpiryRestartRejected("invalid prior coherent snapshot")
    if retained.cohort.truncated_scopes:
        # An incomplete page must not be silently interpreted as full expiry coverage.
        raise CoherentExpiryRestartRejected("prior expiry inventory truncated")
    inventory = tuple(sorted(page.scope_sha256 for page in retained.pages))
    if inventory != retained.cohort.scope_hashes or len(inventory) != len(scopes):
        raise CoherentExpiryRestartRejected("prior expiry scope inventory changed")
    if retained.pages != tuple(sorted(retained.pages, key=lambda page: page.scope_sha256)):
        raise CoherentExpiryRestartRejected("prior expiry pages out of order")

    # Recalculate the coherent digest, not merely the child cohort signature.
    expected = coherent.preview_module._hash(
        "coherent", (coherent._DOMAIN.decode("ascii"), retained.read_at_ms,
                     limit, retained.cohort.cohort_sha256, inventory),
    )
    stable()
    if expected != retained.snapshot_sha256:
        raise CoherentExpiryRestartRejected("retained coherent digest mismatch")
    try:
        current = _ORIGINAL_COHERENT(store, scopes, now_ms=now_ms, limit=limit)
        stable()
        if current.cohort.truncated_scopes:
            raise CoherentExpiryRestartRejected("current expiry inventory truncated")
        if current.cohort.scope_hashes != inventory:
            raise CoherentExpiryRestartRejected("live expiry scope inventory changed")
        transition = _ORIGINAL_RESTART(
            independently_expected_scope_hashes=inventory,
            prior_pages=retained.pages,
            observed_pages=current.pages,
            retained_prior=retained.cohort,
            prior_asserted_now_ms=retained.read_at_ms,
            observed_asserted_now_ms=now_ms,
        )
        stable()
    except (
        coherent.CoherentExpirySnapshotRejected,
        restart.MemoryExpiryRestartRejected,
    ) as exc:
        raise CoherentExpiryRestartRejected(
            "restarted expiry evidence refused; no deletion permitted"
        ) from exc
    if (
        type(transition) is not restart.MemoryExpiryRestartReceipt
        or transition.previous_sha256 != retained.cohort.cohort_sha256
        or transition.observed_sha256 != current.cohort.cohort_sha256
        or transition.candidate_count_before != retained.cohort.candidate_count
        or transition.candidate_count_after != current.cohort.candidate_count
        or transition.automatic_purge_authorized is not False
        or transition.trusted_clock_verified is not False
        or transition.independent_custody_verified is not False
        or transition.cross_scope_atomicity_proven is not False
    ):
        raise CoherentExpiryRestartRejected("coherent restart receipt gained authority")
    payload = json.dumps(
        (retained.snapshot_sha256, current.snapshot_sha256,
         transition.receipt_sha256, transition.status,
         transition.candidate_count_before, transition.candidate_count_after),
        ensure_ascii=True, separators=(",", ":"),
    ).encode("ascii")
    if len(payload) > 4096:
        raise CoherentExpiryRestartRejected("coherent receipt budget exhausted")
    digest = hashlib.sha256(_DOMAIN + payload).hexdigest()
    result = _RESULT(
        retained.snapshot_sha256, current.snapshot_sha256, transition.status,
        transition.candidate_count_before, transition.candidate_count_after, digest,
    )
    _protocol()
    if (
        type(result) is not _RESULT
        or (result.previous_snapshot_sha256, result.observed_snapshot_sha256,
            result.transition, result.previous_candidates,
            result.observed_candidates, result.receipt_sha256) != (
                retained.snapshot_sha256, current.snapshot_sha256,
                transition.status, transition.candidate_count_before,
                transition.candidate_count_after, digest,
            )
        or any(getattr(result, name) is not False for name in (
            "automatic_purge_authorized", "trusted_clock_verified",
            "independent_custody_verified", "historical_completeness_proven",
            "cross_epoch_atomicity_proven",
        ))
    ):
        raise CoherentExpiryRestartRejected("coherent restart gained authority")
    stable()
    return result
