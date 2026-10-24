"""Read-only privacy retention recheck and possible-erasure *review* queue.

A prior inventory is re-created at its exact capture time, then re-evaluated
at the supplied later clock. No Memory content, deletion API or live export
is used. Matching diagnostics are NOT evidence of valid consent, legal basis,
confirmed erasure, backup erasure, or an authenticated wall clock.
"""

from __future__ import annotations

from dataclasses import dataclass, fields

from .memory.contracts import MemoryScope
from .memory.sqlite_store import SQLiteMemoryStore
from .personal_context_retention_review import (
    RetentionState,
    SyntheticRetentionInventory,
    SyntheticRetentionItem,
    review_synthetic_retention_inventory,
)
from .personal_context_revocation_continuity_review import SyntheticRevocationWitness
from .personal_context_revocation_review import SyntheticContextRevocationLedger

_MAX = 2**63 - 1


class SyntheticRetentionRecheckRejected(RuntimeError):
    """The old inventory no longer supports even a diagnostic comparison."""


@dataclass(frozen=True, slots=True)
class SyntheticRetentionRecheck:
    """Possible review cases only; never a deletion command or authorization."""

    scope_digest: str
    captured_inventory_digest: str
    current_inventory_digest: str
    checked_at_ms: int
    expired_memory_ids: tuple[str, ...]
    unbounded_memory_ids: tuple[str, ...]
    scope_revoked: bool

    @property
    def deletion_authorized(self) -> bool:
        return False

    @property
    def erasure_completed(self) -> bool:
        return False

    @property
    def context_use_authorized(self) -> bool:
        return False

    @property
    def external_disclosure_authorized(self) -> bool:
        return False


def _epoch(value: SyntheticRetentionInventory) -> tuple[object, ...]:
    """Pin nested item VALUES, not only references to frozen dataclasses.

    A caller with reflection access can mutate each frozen item in place during
    a subsequent SQLite review. A shallow tuple of the original item objects
    would follow that mutation and fail to notice it.
    """
    if type(value.items) is not tuple or any(
        type(item) is not SyntheticRetentionItem for item in value.items
    ):
        raise SyntheticRetentionRecheckRejected("exact cached retention item types required")
    head = tuple(
        getattr(value, field.name) for field in fields(SyntheticRetentionInventory)
        if field.name != "items"
    )
    items = tuple(
        (item.memory_id, item.revision, item.state) for item in value.items
    )
    return (*head, items)


def review_synthetic_retention_recheck(
    memory: SQLiteMemoryStore,
    scope: MemoryScope,
    revocations: SyntheticContextRevocationLedger,
    cached: SyntheticRetentionInventory,
    *,
    now_ms: int,
    max_age_ms: int,
    retained_revocations: SyntheticRevocationWitness | None = None,
) -> SyntheticRetentionRecheck:
    """Deny modified cached bytes and produce only human-review candidates.

    Four independent Memory/revocation observations narrow visible races.
    They do NOT create a global atomic snapshot; a deletion or revocation can
    occur immediately after the last check. Neither local clock is trusted.
    """
    if (
        type(memory) is not SQLiteMemoryStore
        or type(scope) is not MemoryScope
        or type(revocations) is not SyntheticContextRevocationLedger
        or type(cached) is not SyntheticRetentionInventory
        or type(now_ms) is not int or type(max_age_ms) is not int
        or retained_revocations is not None
        and type(retained_revocations) is not SyntheticRevocationWitness
    ):
        raise SyntheticRetentionRecheckRejected("exact local retention recheck inputs required")
    captured = cached.reviewed_at_ms
    if (
        type(captured) is not int
        or not 0 <= captured <= now_ms <= _MAX
        or not 0 <= max_age_ms <= _MAX
        or now_ms - captured > max_age_ms
    ):
        raise SyntheticRetentionRecheckRejected("cached retention inventory expired")
    pinned = _epoch(cached)
    original_scope = (scope.owner_id, scope.namespace)
    kwargs = {"max_records": 1000, "retained_revocations": retained_revocations}
    before = review_synthetic_retention_inventory(
        memory, scope, revocations, now_ms=captured, **kwargs,
    )
    if before != cached or _epoch(cached) != pinned:
        raise SyntheticRetentionRecheckRejected("cached retention inventory changed")
    current = review_synthetic_retention_inventory(
        memory, scope, revocations, now_ms=now_ms, **kwargs,
    )
    after = review_synthetic_retention_inventory(
        memory, scope, revocations, now_ms=captured, **kwargs,
    )
    last = review_synthetic_retention_inventory(
        memory, scope, revocations, now_ms=now_ms, **kwargs,
    )
    if (
        after != before or last != current
        or _epoch(cached) != pinned
        or (scope.owner_id, scope.namespace) != original_scope
        or current.scope_digest != cached.scope_digest
    ):
        raise SyntheticRetentionRecheckRejected(
            "retention or revocation evidence drifted during diagnostic"
        )
    return SyntheticRetentionRecheck(
        cached.scope_digest, cached.inventory_digest,
        current.inventory_digest, now_ms,
        tuple(item.memory_id for item in current.items if item.state is RetentionState.EXPIRED),
        tuple(item.memory_id for item in current.items if item.state is RetentionState.NO_EXPIRY),
        current.revoked,
    )
