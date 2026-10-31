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
from .personal_context_revocation_continuity_review import SyntheticRevocationWitness
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

    # The independently retained veto prefix belongs to the caller. The
    # lower-level review validates it before the Memory projection, but a
    # later callback could reflectively rewrite its frozen fields. Pin its
    # exact values through the *whole* context reuse operation.
    retained_epoch = None
    if retained_revocations is not None:
        if type(retained_revocations) is not SyntheticRevocationWitness:
            raise SyntheticContextReuseRejected(
                "exact retained revocation witness required"
            )
        retained_revocations.assert_integrity()
        retained_epoch = (
            retained_revocations.rows, retained_revocations.witness_id,
        )

    # Pin both SQLite source carriers BEFORE any reentrant constructors or
    # projections. A constructor that redirects the path must not establish
    # the new value as the expected baseline.
    source_epoch = (store.path, ledger.path)

    # Record the original immutable content structure before callbacks that
    # may attempt reflection-based mutation of a frozen dataclass.
    identity = _cached_bundle_epoch(cached)
    # Snapshot the request/selection intent and database source identities.
    # Frozen dataclasses can still be reflectively mutated by a callback.
    # A matching cached bundle alone does not pin the policy that selected it.
    request_epoch = (
        request.owner_id, request.namespaces, request.text,
        request.per_namespace_limit, request.include_expired,
    )
    policy_epoch = (
        policy.total_limit, policy.per_namespace_limit, policy.policy_revision,
    )
    # Exact object carriers matter, not only equal-valued str/tuple replacements.
    cached_items_epoch = tuple((
        item, item.memory_id, item.namespace, item.content,
        item.revision, item.provenance_id,
    ) for item in cached.items)
    cached_carriers = (cached.items, cached.bundle_id, cached.snapshot_digest)

    def assert_carriers() -> None:
        try:
            current_request = (
                request.owner_id, request.namespaces, request.text,
                request.per_namespace_limit, request.include_expired,
            )
            current_policy = (
                policy.total_limit, policy.per_namespace_limit,
                policy.policy_revision,
            )
            if (
                any(now is not original for now, original in zip(
                    current_request, request_epoch, strict=True,
                ))
                or any(now is not original for now, original in zip(
                    current_policy, policy_epoch, strict=True,
                ))
                or store.path is not source_epoch[0]
                or ledger.path is not source_epoch[1]
                or cached.items is not cached_carriers[0]
                or cached.bundle_id is not cached_carriers[1]
                or cached.snapshot_digest is not cached_carriers[2]
                or len(cached.items) != len(cached_items_epoch)
                or any(
                    current is not item or any(
                        getattr(current, field) is not original
                        for field, original in zip(
                            ("memory_id", "namespace", "content",
                             "revision", "provenance_id"), saved,
                            strict=True,
                        )
                    )
                    for current, (item, *saved) in zip(
                        cached.items, cached_items_epoch, strict=True,
                    )
                )
            ):
                raise SyntheticContextReuseRejected(
                    "context policy, request or source changed during recheck"
                )
        except (AttributeError, TypeError, ValueError) as exc:
            raise SyntheticContextReuseRejected(
                "context policy, request or source changed during recheck"
            ) from exc

    CoherentSnapshotRequest(*request_epoch)
    assert_carriers()
    ContextSelectionPolicy(*policy_epoch)
    assert_carriers()
    fresh = review_fresh_nonrevoked_context(
        store, request, policy, ledger,
        retained_revocations=retained_revocations,
    )
    # A fresh re-projection is a separate reflected-mutable carrier. Pin its
    # nested identity before equality/receipt callbacks: changing an item while
    # preserving bundle_id would otherwise escape the cached-only checks.
    fresh_epoch = _cached_bundle_epoch(fresh)
    fresh_items = fresh.items
    fresh_id, fresh_digest = fresh.bundle_id, fresh.snapshot_digest
    fresh_item_epoch = tuple((
        item, item.memory_id, item.namespace, item.content,
        item.revision, item.provenance_id,
    ) for item in fresh_items)

    def assert_fresh_epoch() -> None:
        if (
            type(fresh) is not SyntheticContextBundle
            or fresh.items is not fresh_items
            or fresh.bundle_id is not fresh_id
            or fresh.snapshot_digest is not fresh_digest
            or _cached_bundle_epoch(fresh) != fresh_epoch
            or any(
                current is not original
                or any(
                    getattr(current, field) is not saved
                    for field, saved in zip(
                        ("memory_id", "namespace", "content",
                         "revision", "provenance_id"), values, strict=True,
                    )
                )
                for current, (original, *values) in zip(
                    fresh.items, fresh_item_epoch, strict=True,
                )
            )
        ):
            raise SyntheticContextReuseRejected(
                "fresh context changed during reuse"
            )

    # Preserve the established cached-projection diagnostic for callers and
    # prior regression fixtures; policy/source drift is a separate veto.
    if cached != fresh or _cached_bundle_epoch(cached) != identity:
        raise SyntheticContextReuseRejected(
            "cached context differs from fresh verified projection"
        )
    assert_carriers()
    if retained_revocations is not None:
        retained_revocations.assert_integrity()
        if (
            retained_revocations.rows, retained_revocations.witness_id,
        ) != retained_epoch:
            raise SyntheticContextReuseRejected(
                "retained revocation witness changed during reuse"
            )
    if (
        request_epoch != (
            request.owner_id, request.namespaces, request.text,
            request.per_namespace_limit, request.include_expired,
        )
        or policy_epoch != (
            policy.total_limit, policy.per_namespace_limit,
            policy.policy_revision,
        )
        or store.path is not source_epoch[0]
        or ledger.path is not source_epoch[1]
    ):
        raise SyntheticContextReuseRejected(
            "context policy, request or source changed during recheck"
        )
    assert_carriers()
    assert_fresh_epoch()
    receipt = SyntheticContextReuseReview(
        fresh.bundle_id, fresh.snapshot_digest, now_ms,
    )
    assert_carriers()
    assert_fresh_epoch()
    if retained_revocations is not None:
        retained_revocations.assert_integrity()
        if (
            retained_revocations.rows is not retained_epoch[0]
            or retained_revocations.witness_id is not retained_epoch[1]
        ):
            raise SyntheticContextReuseRejected(
                "retained revocation witness changed during reuse"
            )
    if (
        type(receipt) is not SyntheticContextReuseReview
        or receipt.bundle_id is not fresh.bundle_id
        or receipt.snapshot_digest is not fresh.snapshot_digest
        or receipt.rechecked_at_ms is not now_ms
    ):
        raise SyntheticContextReuseRejected(
            "context reuse returned receipt changed during construction"
        )
    return receipt
