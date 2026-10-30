"""One-transaction content-free Memory v1 row/event epoch review.

This opt-in, local-only view uses ONE SQLite read transaction, spanning
all requested namespaces and their event rows. Unlike two independently
sampled store readers, it cannot accidentally mix pre/post writer versions
inside that one database. A hash is not external provenance or consent.
No Memory v1 DDL or frozen public API is modified.
"""

from __future__ import annotations

import hashlib
import json
import re
import sqlite3
from contextlib import closing
from dataclasses import dataclass
from pathlib import Path

from .contracts import MemoryRecord, MemorySchemaError, MemoryScope
from .sqlite_store import (
    SQLITE_INT_MAX,
    SQLiteMemoryStore,
    _record,
    _validate_v1_schema,
)

_MAX_SCOPES = 8
_MAX_ROWS_PER_SCOPE = 10_000
_MAX_EVENTS_PER_SCOPE = 10_000
_MEMORY_ID = re.compile(r"mem_[0-9a-f]{64}\Z")
_OPERATIONS = frozenset(("create", "update", "delete", "expire"))
_DOMAIN = b"ARK-memory-single-tx-event-epoch-v1\0"


@dataclass(frozen=True, slots=True)
class AtomicMemoryEpochReview:
    scope_fingerprints: tuple[str, ...]
    row_counts: tuple[int, ...]
    event_counts: tuple[int, ...]
    event_tail_ids: tuple[int, ...]
    epoch_digest: str

    @property
    def independent_writer_proven(self) -> bool:
        return False

    @property
    def cross_store_atomicity_proven(self) -> bool:
        return False

    @property
    def trusted_clock_proven(self) -> bool:
        return False

    @property
    def memory_disclosure_authorized(self) -> bool:
        return False

    @property
    def dispatch_authorized(self) -> bool:
        return False



def _validate_event_causality(
    identities: list[tuple[object, ...]],
    events: list[tuple[object, ...]],
) -> None:
    """Fail closed on a broken *local* v1 create/update/terminal history.

    Re-creation after delete/expire starts a fresh revision-1 lifecycle.
    Event IDs may have gaps from other namespaces. This checks only the
    already-sampled SQLite rows, not who wrote them or external custody.
    """
    live: dict[str, int] = {}
    for _event_id, memory_id, operation, revision, _at_ms in events:
        previous = live.get(memory_id)
        if operation == "create":
            if previous is not None or revision != 1:
                raise MemorySchemaError("Memory epoch event lifecycle invalid")
            live[memory_id] = 1
        elif operation == "update":
            if previous is None or previous >= SQLITE_INT_MAX or revision != previous + 1:
                raise MemorySchemaError("Memory epoch event lifecycle invalid")
            live[memory_id] = revision
        else:  # delete or expire: terminal at the unchanged final revision
            if previous is None or revision != previous:
                raise MemorySchemaError("Memory epoch event lifecycle invalid")
            del live[memory_id]

    observed = {row[0]: row[2] for row in identities}
    if len(observed) != len(identities) or observed != live:
        raise MemorySchemaError("Memory epoch live rows disagree with event lifecycle")


_RESULT_TYPE = AtomicMemoryEpochReview


def review_atomic_memory_epoch(
    store: SQLiteMemoryStore,
    scopes: tuple[MemoryScope, ...],
) -> AtomicMemoryEpochReview:
    """Produce one bounded row/event digest without returning Memory content.

    A pre-clock SELECT anchors the SQLite snapshot. Records and event history
    are observed in the same transaction; this does NOT prove the authenticity
    of writers, retained historical tips, external clocks or other databases.
    """
    if (
        type(store) is not SQLiteMemoryStore
        or type(scopes) is not tuple
        or not 1 <= len(scopes) <= _MAX_SCOPES
        or any(type(s) is not MemoryScope for s in scopes)
    ):
        raise MemorySchemaError("exact bounded Memory epoch inputs required")
    carriers = tuple(scopes)
    pairs = tuple((scope.owner_id, scope.namespace) for scope in carriers)
    if (
        any(type(owner) is not str or type(name) is not str
            for owner, name in pairs)
        or len(set(pairs)) != len(pairs)
        or len(set(owner for owner, _ in pairs)) != 1
        or pairs != tuple(sorted(pairs))
    ):
        raise MemorySchemaError("Memory epoch scopes must be unique ordered same-owner")
    path = store.path
    if not isinstance(path, Path):
        raise MemorySchemaError("Memory epoch requires stable local Path")

    def stable() -> None:
        if (
            store.path is not path
            or len(scopes) != len(carriers)
            or any(
                item is not original
                or type(item) is not MemoryScope
                or item.owner_id is not owner
                or item.namespace is not namespace
                for item, original, (owner, namespace) in zip(
                    scopes, carriers, pairs, strict=True,
                )
            )
        ):
            raise MemorySchemaError("Memory epoch source/scope changed during review")

    stable()
    try:
        resolved = path.resolve()
        stable()
        uri = resolved.as_uri() + "?mode=ro"
        stable()
        connection = sqlite3.connect(uri, uri=True)
    except (OSError, sqlite3.Error) as exc:
        raise MemorySchemaError("cannot open Memory epoch read-only") from exc

    row_counts: list[int] = []
    event_counts: list[int] = []
    event_tail_ids: list[int] = []
    scope_hashes: list[str] = []
    scope_payloads: list[object] = []
    with closing(connection) as conn:
        conn.row_factory = sqlite3.Row
        stable()
        conn.execute("PRAGMA busy_timeout=5000")
        conn.execute("BEGIN")
        stable()
        # Anchor WAL snapshot before a caller-provided clock can write.
        conn.execute("SELECT name FROM sqlite_master ORDER BY name LIMIT 1").fetchone()
        stable()
        _validate_v1_schema(conn)
        stable()
        observed_at_ms = store._now()
        stable()

        for owner, namespace in pairs:
            stable()
            scope_id = hashlib.sha256(
                json.dumps((owner, namespace), ensure_ascii=False,
                           separators=(",", ":")).encode("utf-8")
            ).hexdigest()
            stable()

            record_rows = conn.execute(
                "SELECT * FROM memories WHERE owner_id=? AND namespace=? "
                "ORDER BY memory_id LIMIT ?",
                (owner, namespace, _MAX_ROWS_PER_SCOPE + 1),
            ).fetchall()
            stable()
            if len(record_rows) > _MAX_ROWS_PER_SCOPE:
                raise MemorySchemaError("Memory epoch row scan budget exceeded")
            identities: list[tuple[object, ...]] = []
            for raw in record_rows:
                record = _record(raw)
                stable()
                if (
                    type(record) is not MemoryRecord
                    or type(record.scope) is not MemoryScope
                    or (record.scope.owner_id, record.scope.namespace)
                    != (owner, namespace)
                ):
                    raise MemorySchemaError("Memory epoch decoded row changed scope")
                identities.append((
                    record.memory_id, record.source_id, record.revision,
                    record.content_sha256, raw["metadata_json"],
                    record.created_at_ms, record.updated_at_ms, record.expires_at_ms,
                ))
                stable()

            event_rows = conn.execute(
                "SELECT event_id,memory_id,operation,revision,occurred_at_ms "
                "FROM memory_events WHERE owner_id=? AND namespace=? "
                "ORDER BY event_id LIMIT ?",
                (owner, namespace, _MAX_EVENTS_PER_SCOPE + 1),
            ).fetchall()
            stable()
            if len(event_rows) > _MAX_EVENTS_PER_SCOPE:
                raise MemorySchemaError("Memory epoch event scan budget exceeded")
            events: list[tuple[object, ...]] = []
            last_id = 0
            for raw in event_rows:
                event_id, memory_id, operation, revision, at_ms = tuple(raw)
                if (
                    type(event_id) is not int or not last_id < event_id <= SQLITE_INT_MAX
                    or type(memory_id) is not str
                    or _MEMORY_ID.fullmatch(memory_id) is None
                    or type(operation) is not str or operation not in _OPERATIONS
                    or type(revision) is not int
                    or not 1 <= revision <= SQLITE_INT_MAX
                    or type(at_ms) is not int or not 0 <= at_ms <= SQLITE_INT_MAX
                ):
                    raise MemorySchemaError("Memory epoch invalid persisted event")
                events.append((event_id, memory_id, operation, revision, at_ms))
                last_id = event_id
                stable()

            _validate_event_causality(identities, events)
            row_counts.append(len(identities))
            event_counts.append(len(events))
            event_tail_ids.append(last_id)
            scope_hashes.append(scope_id)
            scope_payloads.append((scope_id, identities, events))
            stable()

        # This read-only transaction contains only metadata and row hashes;
        # it cannot silently publish raw Memory content or make any writes.
        conn.rollback()
    stable()
    payload = (1, observed_at_ms, scope_payloads)
    encoded = json.dumps(
        payload, sort_keys=True, ensure_ascii=False, allow_nan=False,
        separators=(",", ":"),
    ).encode("utf-8")
    stable()
    digest = hashlib.sha256(_DOMAIN + encoded).hexdigest()
    stable()
    fingerprints = tuple(scope_hashes)
    rows = tuple(row_counts)
    events = tuple(event_counts)
    tails = tuple(event_tail_ids)
    review = AtomicMemoryEpochReview(fingerprints, rows, events, tails, digest)
    stable()
    if (
        type(review) is not _RESULT_TYPE
        or review.scope_fingerprints is not fingerprints
        or review.row_counts is not rows
        or review.event_counts is not events
        or review.event_tail_ids is not tails
        or review.epoch_digest is not digest
        or review.independent_writer_proven is not False
        or review.cross_store_atomicity_proven is not False
        or review.trusted_clock_proven is not False
        or review.memory_disclosure_authorized is not False
        or review.dispatch_authorized is not False
    ):
        raise MemorySchemaError("Memory epoch result changed")
    return review
