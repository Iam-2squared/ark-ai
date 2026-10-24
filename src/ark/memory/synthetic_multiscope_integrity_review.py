"""Bounded, single-snapshot cross-namespace Memory integrity review.

Synthetic metadata-only witness: local hashes are not authenticated consent,
past content attestation, deletion proof, or permission to disclose records.
No Memory v1 schema change or writes to SQLite are performed.
"""

from __future__ import annotations

import hashlib
import json
from contextlib import closing
from dataclasses import dataclass

from .contracts import MemoryScope
from .sqlite_store import SQLiteMemoryStore, _record, _validate_v1_schema
from .synthetic_event_continuity_review import (
    SyntheticMemoryEventRejected,
    SyntheticMemoryEventWitness,
    _DIGEST,
    _genesis,
    _hash,
    _scope_digest,
)

_MAX_SCOPES = 16
_MAX_ROWS = 10_000
_MAX_EVENTS = 10_000
_SQLITE_MAX = 2**63 - 1


class SyntheticMemorySnapshotRejected(SyntheticMemoryEventRejected):
    """The offline Memory scope, lifecycle or row snapshot is not coherent."""


def _row_hash(record: object) -> str:
    """Commit to all persisted row values without returning source or content."""
    return _hash(
        "ARK-synthetic-memory-row-v1",
        (
            record.memory_id,
            record.scope.owner_id,
            record.scope.namespace,
            record.source_id,
            record.content_sha256,
            hashlib.sha256(
                json.dumps(
                    dict(record.metadata), ensure_ascii=False,
                    sort_keys=True, separators=(",", ":"),
                ).encode("utf-8")
            ).hexdigest(),
            record.created_at_ms,
            record.updated_at_ms,
            record.expires_at_ms,
            record.revision,
        ),
    )


@dataclass(frozen=True, slots=True)
class SyntheticMemoryScopeDigest:
    scope_digest: str
    events: SyntheticMemoryEventWitness
    live_row_count: int
    live_rows_digest: str

    @property
    def context_use_authorized(self) -> bool:
        return False

    @property
    def deletion_authorized(self) -> bool:
        return False


@dataclass(frozen=True, slots=True)
class SyntheticMemorySnapshotDigest:
    owner_digest: str
    scopes: tuple[SyntheticMemoryScopeDigest, ...]
    snapshot_digest: str

    @property
    def external_disclosure_authorized(self) -> bool:
        return False

    @property
    def context_use_authorized(self) -> bool:
        return False

    @property
    def deletion_authorized(self) -> bool:
        return False


def review_synthetic_memory_scopes(
    store: SQLiteMemoryStore,
    scopes: tuple[MemoryScope, ...],
    *,
    retained_events: tuple[SyntheticMemoryEventWitness, ...] | None = None,
    require_same_snapshot: SyntheticMemorySnapshotDigest | None = None,
) -> SyntheticMemorySnapshotDigest:
    """Check all named namespaces in ONE read-only SQLite transaction.

    `retained_events` permits append-only history growth; it does not prove
    earlier row content. `require_same_snapshot` instead demands an unchanged
    exact snapshot, including all current row hashes, so legitimate new writes
    also require an explicit new review. No clock or backend is called.
    """
    if (
        type(store) is not SQLiteMemoryStore
        or type(scopes) is not tuple
        or not 1 <= len(scopes) <= _MAX_SCOPES
        or any(type(scope) is not MemoryScope for scope in scopes)
    ):
        raise SyntheticMemorySnapshotRejected("exact Memory scope inputs required")
    values = tuple((scope.owner_id, scope.namespace) for scope in scopes)
    if (
        len(set(values)) != len(values)
        or len({owner for owner, _ in values}) != 1
    ):
        raise SyntheticMemorySnapshotRejected("scopes must be distinct and same-owner")
    # Bind values, not frozen dataclass references, before SQLite access.
    pinned = tuple(MemoryScope(owner, namespace) for owner, namespace in values)
    hashes = tuple(_scope_digest(scope) for scope in pinned)
    if retained_events is not None:
        if (
            type(retained_events) is not tuple
            or len(retained_events) != len(pinned)
            or any(type(v) is not SyntheticMemoryEventWitness for v in retained_events)
        ):
            raise SyntheticMemorySnapshotRejected("exact retained event witnesses required")
        for value, digest in zip(retained_events, hashes, strict=True):
            value.assert_shape(digest)
        retained_epoch = tuple(
            (v.scope_digest, v.event_count, v.last_event_id, v.tail_hash)
            for v in retained_events
        )
    else:
        retained_epoch = None
    if require_same_snapshot is not None and (
        type(require_same_snapshot) is not SyntheticMemorySnapshotDigest
        or type(require_same_snapshot.scopes) is not tuple
    ):
        raise SyntheticMemorySnapshotRejected("exact retained snapshot required")
    if require_same_snapshot is not None:
        # Dataclass equality alone is NOT an exact-type shape check: in
        # Python, bool(True) compares equal to integer 1. A reflectively
        # corrupted cached row count could otherwise pass equality checks.
        if (
            type(require_same_snapshot.owner_digest) is not str
            or require_same_snapshot.owner_digest
            != _hash("ARK-synthetic-memory-owner-v1", values[0][0])
            or type(require_same_snapshot.snapshot_digest) is not str
            or not _DIGEST.fullmatch(require_same_snapshot.snapshot_digest)
            or len(require_same_snapshot.scopes) != len(hashes)
        ):
            raise SyntheticMemorySnapshotRejected("malformed cached Memory snapshot")
        for scope_hash, item in zip(
            hashes, require_same_snapshot.scopes, strict=True,
        ):
            if (
                type(item) is not SyntheticMemoryScopeDigest
                or type(item.scope_digest) is not str
                or item.scope_digest != scope_hash
                or type(item.events) is not SyntheticMemoryEventWitness
                or type(item.live_row_count) is not int
                or not 0 <= item.live_row_count <= _MAX_ROWS
                or type(item.live_rows_digest) is not str
                or not _DIGEST.fullmatch(item.live_rows_digest)
            ):
                raise SyntheticMemorySnapshotRejected("malformed cached Memory scope")
            try:
                item.events.assert_shape(scope_hash)
            except SyntheticMemoryEventRejected as exc:
                raise SyntheticMemorySnapshotRejected(
                    "malformed cached Memory event witness"
                ) from exc
    # A copy prevents reflected mutations of a frozen nested receipt from
    # silently turning a comparison of references into a false equality.
    same_epoch = None
    if require_same_snapshot is not None:
        try:
            same_epoch = (
                require_same_snapshot.owner_digest,
                require_same_snapshot.snapshot_digest,
                tuple((
                    item.scope_digest,
                    item.events.scope_digest, item.events.event_count,
                    item.events.last_event_id, item.events.tail_hash,
                    item.live_row_count, item.live_rows_digest,
                ) for item in require_same_snapshot.scopes),
            )
        except (AttributeError, TypeError) as exc:
            raise SyntheticMemorySnapshotRejected("invalid retained snapshot") from exc

    path_epoch = store.path
    results = []
    with closing(store._connect_readonly()) as conn:
        conn.execute("BEGIN")
        try:
            _validate_v1_schema(conn)
            for scope, scope_hash in zip(pinned, hashes, strict=True):
                raw_events = conn.execute(
                    """SELECT event_id,memory_id,owner_id,namespace,operation,
                              revision,occurred_at_ms FROM memory_events
                       WHERE owner_id=? AND namespace=?
                       ORDER BY event_id LIMIT ?""",
                    (scope.owner_id, scope.namespace, _MAX_EVENTS + 1),
                ).fetchall()
                if len(raw_events) > _MAX_EVENTS:
                    raise SyntheticMemorySnapshotRejected("event budget exceeded")
                previous = SyntheticMemoryEventWitness(
                    scope_hash, 0, 0, _genesis(scope_hash),
                )
                prefixes = [previous]
                states: dict[str, tuple[bool, int]] = {}
                last_id = 0
                for event in raw_events:
                    event_id, memory_id, owner, namespace, op, revision, at = event
                    if (
                        type(event_id) is not int
                        or not last_id < event_id <= _SQLITE_MAX
                        or type(memory_id) is not str
                        or not memory_id.startswith("mem_")
                        or len(memory_id) != 68
                        or any(c not in "0123456789abcdef" for c in memory_id[4:])
                        or (owner, namespace) != (scope.owner_id, scope.namespace)
                        or type(op) is not str
                        or op not in ("create", "update", "delete", "expire")
                        or type(revision) is not int
                        or not 1 <= revision <= _SQLITE_MAX
                        or type(at) is not int or not 0 <= at <= _SQLITE_MAX
                    ):
                        raise SyntheticMemorySnapshotRejected("malformed Memory event")
                    alive, prior_revision = states.get(memory_id, (False, 0))
                    if op == "create":
                        if alive or revision != 1:
                            raise SyntheticMemorySnapshotRejected("invalid create transition")
                        states[memory_id] = (True, revision)
                    elif op == "update":
                        if not alive or revision != prior_revision + 1:
                            raise SyntheticMemorySnapshotRejected("invalid update transition")
                        states[memory_id] = (True, revision)
                    else:
                        if not alive or revision != prior_revision:
                            raise SyntheticMemorySnapshotRejected("invalid terminal transition")
                        states[memory_id] = (False, revision)
                    previous = SyntheticMemoryEventWitness(
                        scope_hash, previous.event_count + 1, event_id,
                        _hash("ARK-synthetic-memory-event-v1",
                              (previous.tail_hash, tuple(event))),
                    )
                    prefixes.append(previous)
                    last_id = event_id
                raw_rows = conn.execute(
                    """SELECT * FROM memories WHERE owner_id=? AND namespace=?
                       ORDER BY memory_id LIMIT ?""",
                    (scope.owner_id, scope.namespace, _MAX_ROWS + 1),
                ).fetchall()
                if len(raw_rows) > _MAX_ROWS:
                    raise SyntheticMemorySnapshotRejected("row budget exceeded")
                live = {}
                row_hashes = []
                for raw_row in raw_rows:
                    record = _record(raw_row)
                    if record.scope != scope or record.memory_id in live:
                        raise SyntheticMemorySnapshotRejected("Memory row scope or ID mismatch")
                    live[record.memory_id] = record.revision
                    row_hashes.append(_row_hash(record))
                expected = {
                    key: revision for key, (alive, revision) in states.items() if alive
                }
                if live != expected:
                    raise SyntheticMemorySnapshotRejected("event and live rows disagree")
                if retained_events is not None:
                    older = retained_events[len(results)]
                    if (
                        older.event_count >= len(prefixes)
                        or prefixes[older.event_count] != older
                    ):
                        raise SyntheticMemorySnapshotRejected("retained event prefix changed")
                results.append(SyntheticMemoryScopeDigest(
                    scope_hash, previous, len(row_hashes),
                    _hash("ARK-synthetic-memory-live-rows-v1", tuple(row_hashes)),
                ))
            conn.commit()
        except BaseException:
            conn.rollback()
            raise
    owner_digest = _hash("ARK-synthetic-memory-owner-v1", values[0][0])
    snapshot = SyntheticMemorySnapshotDigest(
        owner_digest, tuple(results),
        _hash("ARK-synthetic-memory-multiscope-v1", (
            owner_digest,
            tuple((
                row.scope_digest, row.events.tail_hash,
                row.events.event_count, row.events.last_event_id,
                row.live_row_count, row.live_rows_digest,
            ) for row in results),
        )),
    )
    if store.path != path_epoch or tuple(
        (scope.owner_id, scope.namespace) for scope in scopes
    ) != values:
        raise SyntheticMemorySnapshotRejected("Memory scope or source changed")
    if retained_events is not None and tuple(
        (v.scope_digest, v.event_count, v.last_event_id, v.tail_hash)
        for v in retained_events
    ) != retained_epoch:
        raise SyntheticMemorySnapshotRejected("retained Memory event witness changed")
    if require_same_snapshot is not None:
        current_epoch = (
            require_same_snapshot.owner_digest,
            require_same_snapshot.snapshot_digest,
            tuple((
                item.scope_digest,
                item.events.scope_digest, item.events.event_count,
                item.events.last_event_id, item.events.tail_hash,
                item.live_row_count, item.live_rows_digest,
            ) for item in require_same_snapshot.scopes),
        )
        if current_epoch != same_epoch or require_same_snapshot != snapshot:
            raise SyntheticMemorySnapshotRejected("retained exact Memory snapshot changed")
    return snapshot
