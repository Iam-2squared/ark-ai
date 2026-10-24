"""Read-only freshness veto for reusing a previously projected local context.

This fixture re-reads Memory and the synthetic revocation ledger. It never
returns permission to use, disclose, send or execute personal information.
Caller-provided timestamps are NOT authenticated clocks; even a successful
review can race with later revocation or changes across separate databases.
"""

from __future__ import annotations

from dataclasses import dataclass

from .memory.coherent_snapshot_review import CoherentSnapshotRequest
from .memory.sqlite_store import SQLiteMemoryStore
from .personal_context_review import (
    ContextSelectionPolicy,
    SyntheticContextBundle,
    SyntheticContextItem,
)
from .personal_context_revocation_review import (
    SyntheticContextRevocationLedger,
    review_fresh_nonrevoked_context,
)

_MAX = 2**63 - 1


class SyntheticContextReuseRejected(RuntimeError):
    """The old projection cannot be safely revalidated even as a fixture."""


@dataclass(frozen=True, slots=True)
class SyntheticContextReuseReview:
    """Content-free diagnostic receipt; never consent or data-use authority."""

    bundle_id: str
    snapshot_digest: str
    rechecked_at_ms: int

    @property
    def context_use_authorized(self) -> bool:
        return False

    @property
    def external_disclosure_authorized(self) -> bool:
        return False

    @property
    def dispatch_authorized(self) -> bool:
        return False


def _cached_bundle_epoch(cached: SyntheticContextBundle) -> tuple[object, ...]:
    """Pin nested scalar values, not just frozen dataclass/container references.

    Reflection can change an item's fields during a later Memory callback and
    restore a previously invalid cached projection just before equality. This
    is a local tamper fence, not authentication of historic Memory content.
    """
    if (
        type(cached.items) is not tuple or len(cached.items) > 100
        or type(cached.bundle_id) is not str
        or type(cached.snapshot_digest) is not str
    ):
        raise SyntheticContextReuseRejected("cached context shape changed")
    items = []
    for item in cached.items:
        if (
            type(item) is not SyntheticContextItem
            or type(item.memory_id) is not str
            or type(item.namespace) is not str
            or type(item.content) is not str
            or type(item.revision) is not int or item.revision < 1
            or type(item.provenance_id) is not str
        ):
            raise SyntheticContextReuseRejected("cached context item shape changed")
        items.append((
            item, item.memory_id, item.namespace, item.content,
            item.revision, item.provenance_id,
        ))
    return (cached.bundle_id, cached.snapshot_digest, cached.items, tuple(items))


def review_synthetic_context_reuse(
    store: SQLiteMemoryStore,
    request: CoherentSnapshotRequest,
    policy: ContextSelectionPolicy,
    ledger: SyntheticContextRevocationLedger,
    cached: SyntheticContextBundle,
    *,
    captured_at_ms: int,
    now_ms: int,
    max_age_ms: int,
    retained_revocations: object | None = None,
) -> SyntheticContextReuseReview:
    """Refuse stale, revoked or changed cached context; no permission granted.

    Each successful call obtains a fresh coherent Memory snapshot and brackets
    it with persistent veto checks. An earlier independently retained witness
    can detect deletions of previously recorded vetoes. Timestamps are only
    synthetic input checks, not trustworthy elapsed-time evidence.
    """
    if (
        type(store) is not SQLiteMemoryStore
        or type(request) is not CoherentSnapshotRequest
        or type(policy) is not ContextSelectionPolicy
        or type(ledger) is not SyntheticContextRevocationLedger
        or type(cached) is not SyntheticContextBundle
        or any(type(value) is not int for value in (
            captured_at_ms, now_ms, max_age_ms,
        ))
    ):
        raise SyntheticContextReuseRejected("exact synthetic context inputs required")
    if (
        not 0 <= captured_at_ms <= now_ms <= _MAX
        or not 0 <= max_age_ms <= _MAX
        or now_ms - captured_at_ms > max_age_ms
    ):
        raise SyntheticContextReuseRejected("cached context age or clock invalid")

    # Record the original immutable content structure before callbacks that
    # may attempt reflection-based mutation of a frozen dataclass.
    identity = _cached_bundle_epoch(cached)
    fresh = review_fresh_nonrevoked_context(
        store, request, policy, ledger,
        retained_revocations=retained_revocations,
    )
    if cached != fresh or _cached_bundle_epoch(cached) != identity:
        raise SyntheticContextReuseRejected(
            "cached context differs from fresh verified projection"
        )
    return SyntheticContextReuseReview(
        fresh.bundle_id, fresh.snapshot_digest, now_ms,
    )
