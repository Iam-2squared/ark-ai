"""Read-only, content-minimized retention inventory for synthetic local Memory.

This diagnostic cannot erase Memory, audit logs, backups or cached bundles.
A retained veto witness protects only independently preserved local history;
two SQLite files cannot form one atomic snapshot and caller time is untrusted.
"""

from __future__ import annotations

import hashlib
import json
from contextlib import closing
from dataclasses import dataclass
from enum import StrEnum
from pathlib import Path

from .memory.contracts import MemoryScope
from .memory.sqlite_store import SQLiteMemoryStore, _record, _validate_v1_schema
from .personal_context_revocation_continuity_review import (
    SyntheticRevocationWitness,
    review_revocation_continuity,
)
from .personal_context_revocation_review import (
    SyntheticContextRevocationLedger,
    _scope_digest,
)

_MAX = 2**63 - 1


class SyntheticRetentionRejected(RuntimeError):
    """An offline Memory retention inventory cannot be trusted."""


class RetentionState(StrEnum):
    EXPIRED = "expired"
    NOT_EXPIRED = "not_expired"
    NO_EXPIRY = "no_expiry"


@dataclass(frozen=True, slots=True)
class SyntheticRetentionItem:
    memory_id: str
    revision: int
    state: RetentionState


@dataclass(frozen=True, slots=True)
class SyntheticRetentionInventory:
    scope_digest: str
    inventory_digest: str
    reviewed_at_ms: int
    revoked: bool
    items: tuple[SyntheticRetentionItem, ...]

    @property
    def expired_count(self) -> int:
        return sum(item.state is RetentionState.EXPIRED for item in self.items)

    @property
    def erasure_completed(self) -> bool:
        return False

    @property
    def deletion_authorized(self) -> bool:
        return False

    @property
    def context_use_authorized(self) -> bool:
        return False


def review_synthetic_retention_inventory(
    memory: SQLiteMemoryStore,
    scope: MemoryScope,
    ledger: SyntheticContextRevocationLedger,
    *,
    now_ms: int,
    max_records: int = 1000,
    retained_revocations: SyntheticRevocationWitness | None = None,
) -> SyntheticRetentionInventory:
    """Inventory exact local revisions, expiry and veto without deleting data.

    Expiry is inclusive: expires_at_ms <= now_ms is EXPIRED. Unbounded
    retention is flagged NO_EXPIRY for future human policy review, not
    treated as consent. A successful diagnostic never authorizes purging.
    """
    if (
        type(memory) is not SQLiteMemoryStore
        or type(scope) is not MemoryScope
        or type(ledger) is not SyntheticContextRevocationLedger
        or type(now_ms) is not int or not 0 <= now_ms <= _MAX
        or type(max_records) is not int or not 1 <= max_records <= 1000
    ):
        raise SyntheticRetentionRejected("exact bounded retention inputs required")
    # The FIRST scope hashing callback can be reentrant. Pin the original
    # caller carriers and both independent SQLite sources before invoking it.
    original_owner = scope.owner_id
    original_namespace = scope.namespace
    epoch = (original_owner, original_namespace)
    memory_source = memory.path
    veto_source = ledger.path
    pinned = MemoryScope(*epoch)
    scope_hash = _scope_digest(pinned)
    if not isinstance(memory_source, Path) or not isinstance(veto_source, Path):
        raise SyntheticRetentionRejected("retention source path is invalid")
    retained_epoch = None
    retained_rows_carrier = None
    if retained_revocations is not None:
        if type(retained_revocations) is not SyntheticRevocationWitness:
            raise SyntheticRetentionRejected("exact retained revocation witness required")
        # Retain the exact historical source before the FIRST potentially
        # reentrant integrity callback. Its result cannot reset our baseline.
        retained_rows_carrier = retained_revocations.rows
        retained_epoch = (
            retained_rows_carrier, retained_revocations.witness_id,
        )

    def assert_sources() -> None:
        if memory.path is not memory_source or ledger.path is not veto_source:
            raise SyntheticRetentionRejected(
                "retention evidence source changed during inventory"
            )
        if (
            scope.owner_id is not original_owner
            or scope.namespace is not original_namespace
            or (scope.owner_id, scope.namespace) != epoch
        ):
            raise SyntheticRetentionRejected("retention scope changed during inventory")
        if retained_revocations is not None and (
            retained_revocations.rows is not retained_rows_carrier
            or (retained_revocations.rows, retained_revocations.witness_id)
            != retained_epoch
        ):
            raise SyntheticRetentionRejected(
                "retained revocation witness changed during inventory"
            )

    assert_sources()
    if retained_revocations is not None:
        retained_revocations.assert_integrity()
        assert_sources()
    first = review_revocation_continuity(ledger, retained=retained_revocations)
    assert_sources()
    with closing(memory._connect_readonly()) as conn:
        assert_sources()
        conn.execute("BEGIN")
        try:
            _validate_v1_schema(conn)
            assert_sources()
            rows = conn.execute(
                """SELECT * FROM memories WHERE owner_id=? AND namespace=?
                   ORDER BY memory_id LIMIT ?""",
                (*epoch, max_records + 1),
            ).fetchall()
            if len(rows) > max_records:
                raise SyntheticRetentionRejected("retention inventory budget exceeded")
            selected: list[SyntheticRetentionItem] = []
            item_epoch: list[tuple[SyntheticRetentionItem, str, int, RetentionState]] = []

            def assert_item_epoch() -> None:
                # A retained diagnostic item is mutable through reflective
                # operations even when the dataclass is frozen. Its values
                # must continue to match the bytes used for the inventory
                # digest across later row and veto callbacks.
                if len(selected) != len(item_epoch) or any(
                    type(item) is not SyntheticRetentionItem
                    or item is not original
                    or (item.memory_id, item.revision, item.state) != (
                        identity, revision, state,
                    )
                    for item, (original, identity, revision, state) in zip(
                        selected, item_epoch, strict=True,
                    )
                ):
                    raise SyntheticRetentionRejected(
                        "retention inventory items changed during review"
                    )

            bound_rows: list[tuple[object, ...]] = []
            for row in rows:
                assert_item_epoch()
                record = _record(row)
                assert_item_epoch()
                if record.scope != pinned or record.updated_at_ms > now_ms:
                    raise SyntheticRetentionRejected(
                        "retention scope or caller clock is inconsistent"
                    )
                if record.expires_at_ms is None:
                    state = RetentionState.NO_EXPIRY
                elif record.expires_at_ms <= now_ms:
                    state = RetentionState.EXPIRED
                else:
                    state = RetentionState.NOT_EXPIRED
                item = SyntheticRetentionItem(
                    record.memory_id, record.revision, state,
                )
                selected.append(item)
                item_epoch.append((item, item.memory_id, item.revision, item.state))
                # Bind hidden row identity without exposing the content or metadata.
                # A coherent byte edit with an unchanged revision/state must change
                # the offline receipt, even if this local row still passes _record.
                metadata_json = json.dumps(
                    dict(record.metadata), ensure_ascii=False,
                    sort_keys=True, separators=(",", ":"),
                ).encode("utf-8")
                assert_item_epoch()
                bound_rows.append((
                    record.memory_id, record.revision, record.content_sha256,
                    hashlib.sha256(metadata_json).hexdigest(),
                    record.created_at_ms, record.updated_at_ms,
                    record.expires_at_ms, state.value,
                ))
            assert_item_epoch()
            assert_sources()
            conn.commit()
        except BaseException:
            conn.rollback()
            raise
    # This second review fences prior veto deletion during the Memory read.
    # Newly appended revocations are allowed but must be reflected in output.
    second = review_revocation_continuity(ledger, retained=first)
    assert_sources()
    assert_item_epoch()
    if (scope.owner_id, scope.namespace) != epoch:
        raise SyntheticRetentionRejected("retention scope changed during inventory")
    revoked = scope_hash in {row[0] for row in second.rows}
    items = tuple(selected)
    payload = json.dumps(
        (
            "ARK-offline-retention-inventory-v2", scope_hash, now_ms, revoked,
            bound_rows,
            second.witness_id,
        ),
        ensure_ascii=True, separators=(",", ":"), allow_nan=False,
    ).encode("utf-8")
    assert_sources()
    assert_item_epoch()
    digest = "retention_" + hashlib.sha256(payload).hexdigest()
    # Hash constructors / hexdigest and dataclass construction are distinct
    # callback edges; neither may silently rebase previously reviewed rows.
    assert_sources()
    assert_item_epoch()
    result = SyntheticRetentionInventory(
        scope_hash, digest, now_ms, revoked, items,
    )
    assert_sources()
    assert_item_epoch()
    if (
        type(result) is not SyntheticRetentionInventory
        or result.scope_digest != scope_hash
        or result.inventory_digest != digest
        or result.reviewed_at_ms != now_ms
        or result.revoked is not revoked
        or result.items is not items
        # Even an exact inventory DTO can have class properties spoofed by
        # a reentrant fixture. Retention review never proves authorization.
        or result.erasure_completed is not False
        or result.deletion_authorized is not False
        or result.context_use_authorized is not False
    ):
        raise SyntheticRetentionRejected("retention inventory result changed")
    return result
