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
    epoch = (scope.owner_id, scope.namespace)
    pinned = MemoryScope(*epoch)
    scope_hash = _scope_digest(pinned)
    first = review_revocation_continuity(ledger, retained=retained_revocations)
    with closing(memory._connect_readonly()) as conn:
        conn.execute("BEGIN")
        try:
            _validate_v1_schema(conn)
            rows = conn.execute(
                """SELECT * FROM memories WHERE owner_id=? AND namespace=?
                   ORDER BY memory_id LIMIT ?""",
                (*epoch, max_records + 1),
            ).fetchall()
            if len(rows) > max_records:
                raise SyntheticRetentionRejected("retention inventory budget exceeded")
            selected: list[SyntheticRetentionItem] = []
            bound_rows: list[tuple[object, ...]] = []
            for row in rows:
                record = _record(row)
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
                selected.append(SyntheticRetentionItem(
                    record.memory_id, record.revision, state,
                ))
                # Bind hidden row identity without exposing the content or metadata.
                # A coherent byte edit with an unchanged revision/state must change
                # the offline receipt, even if this local row still passes _record.
                metadata_json = json.dumps(
                    dict(record.metadata), ensure_ascii=False,
                    sort_keys=True, separators=(",", ":"),
                ).encode("utf-8")
                bound_rows.append((
                    record.memory_id, record.revision, record.content_sha256,
                    hashlib.sha256(metadata_json).hexdigest(),
                    record.created_at_ms, record.updated_at_ms,
                    record.expires_at_ms, state.value,
                ))
            conn.commit()
        except BaseException:
            conn.rollback()
            raise
    # This second review fences prior veto deletion during the Memory read.
    # Newly appended revocations are allowed but must be reflected in output.
    second = review_revocation_continuity(ledger, retained=first)
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
    return SyntheticRetentionInventory(
        scope_hash, "retention_" + hashlib.sha256(payload).hexdigest(),
        now_ms, revoked, items,
    )
