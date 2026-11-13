"""Read-only privacy retention recheck and possible-erasure *review* queue.

A prior inventory is re-created at its exact capture time, then re-evaluated
at the supplied later clock. No Memory content, deletion API or live export
is used. Matching diagnostics are NOT evidence of valid consent, legal basis,
confirmed erasure, backup erasure, or an authenticated wall clock.
"""

from __future__ import annotations

from dataclasses import dataclass, fields
from pathlib import Path

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
_MAX_CACHED_ITEMS = 1000  # Same upper bound as the underlying inventory query.
_HEX = frozenset("0123456789abcdef")


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


_RESULT_TYPE = SyntheticRetentionRecheck
_DENIAL_NAMES = (
    "deletion_authorized", "erasure_completed",
    "context_use_authorized", "external_disclosure_authorized",
)
# Pin the ORIGINAL definitions at import, before an untrusted caller can
# install a False-only stand-in. Capturing them only after four SQLite reads
# would wrongly bless a preinstalled substitute as the expected descriptor.
_ORIGINAL_DENIAL_DESCRIPTORS = tuple(
    vars(_RESULT_TYPE)[key] for key in _DENIAL_NAMES
)
# Result slots and inherited lookup hooks can be replaced even on a frozen
# dataclass. A forged descriptor may read or leak private inventory fields
# before a later False-only authority check. Verify its import-time identity
# BEFORE the first personal-context SQLite projection.
_RESULT_FIELDS = (
    "scope_digest", "captured_inventory_digest", "current_inventory_digest",
    "checked_at_ms", "expired_memory_ids", "unbounded_memory_ids",
    "scope_revoked",
)
# A replaced dataclass constructor can inspect private retention diagnostics
# before the post-construction authority checks. Pin it at import too.
_RESULT_HOOKS = ("__init__", "__new__", "__getattribute__", "__getattr__")
_ORIGINAL_RESULT_FIELDS = tuple(vars(_RESULT_TYPE)[key] for key in _RESULT_FIELDS)
_ORIGINAL_RESULT_HOOKS = tuple(
    vars(_RESULT_TYPE).get(key) for key in _RESULT_HOOKS
)


def _assert_original_denials() -> None:
    if (
        SyntheticRetentionRecheck is not _RESULT_TYPE
        or any(
            vars(_RESULT_TYPE).get(key) is not descriptor
            for names, originals in (
                (_DENIAL_NAMES, _ORIGINAL_DENIAL_DESCRIPTORS),
                (_RESULT_FIELDS, _ORIGINAL_RESULT_FIELDS),
                (_RESULT_HOOKS, _ORIGINAL_RESULT_HOOKS),
            )
            for key, descriptor in zip(names, originals, strict=True)
        )
    ):
        raise SyntheticRetentionRecheckRejected(
            "retention recheck returned result changed: original denial implementation"
        )


def _epoch(value: SyntheticRetentionInventory) -> tuple[object, ...]:
    """Pin nested item VALUES, not only references to frozen dataclasses.

    A caller with reflection access can mutate each frozen item in place during
    a subsequent SQLite review. A shallow tuple of the original item objects
    would follow that mutation and fail to notice it.
    """
    if (
        type(value) is not SyntheticRetentionInventory
        or type(value.scope_digest) is not str
        or len(value.scope_digest) != 64
        or any(char not in _HEX for char in value.scope_digest)
        or type(value.inventory_digest) is not str
        or not value.inventory_digest.startswith("retention_")
        or len(value.inventory_digest) != 74
        or any(char not in _HEX for char in value.inventory_digest[10:])
        or type(value.reviewed_at_ms) is not int
        or not 0 <= value.reviewed_at_ms <= _MAX
        or type(value.revoked) is not bool
        or type(value.items) is not tuple
        or len(value.items) > _MAX_CACHED_ITEMS
    ):
        raise SyntheticRetentionRecheckRejected(
            "exact cached retention inventory fields required"
        )
    if any(
        type(item) is not SyntheticRetentionItem
        or type(item.memory_id) is not str
        or type(item.revision) is not int
        or not 1 <= item.revision <= _MAX
        or type(item.state) is not RetentionState
        for item in value.items
    ):
        # RetentionState extends str and bool extends int. Value-only epoch
        # equality would accept e.g. "not_expired" in place of the enum,
        # or True in place of revision 1, as a supposedly intact receipt.
        raise SyntheticRetentionRecheckRejected("exact cached retention item types required")
    # The persisted inventory is ordered by canonical deterministic Memory ID.
    # A reflected cached receipt can instead contain a huge, malformed,
    # duplicate, or permuted identity. Reject that before any private SQLite
    # or revocation read, without invoking user-controlled equality/hash code.
    ids = tuple(item.memory_id for item in value.items)
    if any(
        len(identity) != 68 or not identity.startswith("mem_")
        or any(char not in _HEX for char in identity[4:])
        for identity in ids
    ) or ids != tuple(sorted(set(ids))):
        raise SyntheticRetentionRecheckRejected(
            "exact cached retention item identity or order required"
        )
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
    _assert_original_denials()
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
    # Equality of inventory values is insufficient when reflected mutation
    # replaces the original tuple or a frozen item with a value-equal clone.
    # Keep independent carrier references before any SQLite/reviewer callback.
    cached_items = cached.items
    cached_item_carriers = tuple(cached_items)
    cached_head_carriers = tuple(
        getattr(cached, field.name) for field in fields(SyntheticRetentionInventory)
        if field.name != "items"
    )
    cached_item_fields = tuple(
        (item.memory_id, item.revision, item.state) for item in cached_items
    )
    original_scope = (scope.owner_id, scope.namespace)
    # Every inventory pins its own sources, but a caller can reflectively
    # retarget a Path *between* the four otherwise coherent inventory reads.
    # Bind both store identities before the first reentrant review.
    memory_source = memory.path
    revocation_source = revocations.path
    if not isinstance(memory_source, Path) or not isinstance(revocation_source, Path):
        raise SyntheticRetentionRecheckRejected("exact retention sources required")
    retained_rows = (
        None if retained_revocations is None else retained_revocations.rows
    )
    retained_epoch = None if retained_revocations is None else (
        retained_revocations.rows, retained_revocations.witness_id,
    )

    def assert_epoch() -> None:
        _assert_original_denials()
        if (
            memory.path is not memory_source
            or revocations.path is not revocation_source
            or scope.owner_id is not original_scope[0]
            or scope.namespace is not original_scope[1]
            or (scope.owner_id, scope.namespace) != original_scope
            or any(
                getattr(cached, field.name) is not original
                for field, original in zip(
                    (field for field in fields(SyntheticRetentionInventory)
                     if field.name != "items"),
                    cached_head_carriers, strict=True,
                )
            )
            or _epoch(cached) != pinned
            or cached.items is not cached_items
            or any(
                item is not original or any(
                    value is not prior
                    for value, prior in zip(
                        (item.memory_id, item.revision, item.state),
                        expected_fields, strict=True,
                    )
                )
                for item, original, expected_fields in zip(
                    cached.items, cached_item_carriers, cached_item_fields, strict=True,
                )
            )
            or (
                retained_revocations is not None
                and retained_revocations.rows is not retained_rows
            )
            or retained_revocations is not None and (
                retained_revocations.witness_id is not retained_epoch[1]
            )
            or retained_epoch != (
                None if retained_revocations is None else (
                    retained_revocations.rows, retained_revocations.witness_id,
                )
            )
        ):
            raise SyntheticRetentionRecheckRejected(
                "retention source or evidence changed during diagnostic"
            )

    kwargs = {"max_records": 1000, "retained_revocations": retained_revocations}
    before = review_synthetic_retention_inventory(
        memory, scope, revocations, now_ms=captured, **kwargs,
    )
    assert_epoch()
    # Dataclass equality is replaceable and is not an integrity check.
    # Compare the independently re-read value fields against the pinned
    # cached epoch, without trusting SyntheticRetentionInventory.__eq__.
    if _epoch(before) != pinned:
        raise SyntheticRetentionRecheckRejected("cached retention inventory changed")
    current = review_synthetic_retention_inventory(
        memory, scope, revocations, now_ms=now_ms, **kwargs,
    )
    assert_epoch()
    current_epoch = _epoch(current)
    current_items = current.items
    current_item_carriers = tuple(current_items)
    after = review_synthetic_retention_inventory(
        memory, scope, revocations, now_ms=captured, **kwargs,
    )
    assert_epoch()
    last = review_synthetic_retention_inventory(
        memory, scope, revocations, now_ms=now_ms, **kwargs,
    )
    assert_epoch()
    if (
        _epoch(after) != pinned or _epoch(last) != current_epoch
        or _epoch(current) != current_epoch
        or current.items is not current_items
        or any(
            item is not original for item, original in zip(
                current.items, current_item_carriers, strict=True,
            )
        )
        or _epoch(cached) != pinned
        or (scope.owner_id, scope.namespace) != original_scope
        or current.scope_digest != cached.scope_digest
    ):
        raise SyntheticRetentionRecheckRejected(
            "retention or revocation evidence drifted during diagnostic"
        )
    # The detached review constructor is a final reentrant boundary. Pin
    # every returned diagnostic carrier and the independently observed
    # current inventory; neither a forged erasure queue nor an equal-valued
    # replacement may escape as a successful local review.
    scope_digest = cached.scope_digest
    captured_digest = cached.inventory_digest
    current_digest = current.inventory_digest
    expired_ids = tuple(
        item.memory_id for item in current.items if item.state is RetentionState.EXPIRED
    )
    unbounded_ids = tuple(
        item.memory_id for item in current.items if item.state is RetentionState.NO_EXPIRY
    )
    revoked = current.revoked
    assert_epoch()
    result = SyntheticRetentionRecheck(
        scope_digest, captured_digest, current_digest, now_ms,
        expired_ids, unbounded_ids, revoked,
    )
    assert_epoch()
    if (
        _epoch(current) != current_epoch
        or current.items is not current_items
        or any(
            item is not original for item, original in zip(
                current.items, current_item_carriers, strict=True,
            )
        )
        or current.scope_digest != scope_digest
        or current.inventory_digest is not current_digest
        or current.revoked is not revoked
    ):
        raise SyntheticRetentionRecheckRejected(
            "current retention evidence changed during result construction"
        )
    # Every denial property is an overridable callback in test fixtures.
    # A False return can still mutate already-checked cached/current evidence,
    # result fields or an earlier authority descriptor. Validate the original
    # carriers after EACH callback, including the last one.
    def assert_result_epoch() -> None:
        assert_epoch()
        if (
            _epoch(current) != current_epoch
            or current.items is not current_items
            or any(
                item is not original for item, original in zip(
                    current.items, current_item_carriers, strict=True,
                )
            )
            # Cached and current inventories are separately constructed:
            # the same scope digest VALUE need not share a str object.
            or current.scope_digest != scope_digest
            or current.inventory_digest is not current_digest
            or current.revoked is not revoked
            or type(result) is not _RESULT_TYPE
            or result.scope_digest is not scope_digest
            or result.captured_inventory_digest is not captured_digest
            or result.current_inventory_digest is not current_digest
            or type(result.checked_at_ms) is not int
            or result.checked_at_ms is not now_ms
            or type(result.expired_memory_ids) is not tuple
            or result.expired_memory_ids is not expired_ids
            or type(result.unbounded_memory_ids) is not tuple
            or result.unbounded_memory_ids is not unbounded_ids
            or type(result.scope_revoked) is not bool
            or result.scope_revoked is not revoked
            or any(
                getattr(_RESULT_TYPE, key) is not descriptor
                for key, descriptor in zip(
                    _DENIAL_NAMES, _ORIGINAL_DENIAL_DESCRIPTORS, strict=True,
                )
            )
        ):
            raise SyntheticRetentionRecheckRejected(
                "retention recheck returned result changed during construction"
            )

    assert_result_epoch()
    for authority in _DENIAL_NAMES:
        if getattr(result, authority) is not False:
            raise SyntheticRetentionRecheckRejected(
                "retention recheck returned result changed during construction"
            )
        assert_result_epoch()
    return result
