"""Read-only retained Memory row commitments across unrelated event appends.

The caller must preserve the earlier witness outside the SQLite database.
One transaction observes both current live rows and event history, detects a
silent old-row edit even when a *different* memory has appended an event, and
rejects an altered historical event prefix. A new event for a row is only an
explanation for possible change, NOT proof of a legitimate writer or content.
This reviewer neither authenticates witnesses nor authorizes disclosure.
"""

from __future__ import annotations

import hashlib
import json
import sqlite3
from contextlib import closing
from dataclasses import dataclass

from . import sqlite_event_prefix_review as prefix
from .contracts import MemorySchemaError
from .sqlite_store import SQLiteMemoryStore, _record, _validate_v1_schema

_MAX_ROWS = 10_000
_MAX_EVENTS = 40_000
_DOMAIN = b"ARK-retained-memory-row-delta-v1\0"


class MemoryRowDeltaRejected(MemorySchemaError):
    """Retained Memory row history is missing, inconsistent or unauthorized."""


@dataclass(frozen=True, slots=True)
class MemoryRowDeltaWitness:
    event_count: int
    last_event_id: int
    event_prefix_sha256: str
    rows: tuple[tuple[str, int, str], ...]

    @property
    def independently_authenticated(self) -> bool:
        return False

    @property
    def historical_writer_authenticated(self) -> bool:
        return False

    @property
    def disclosure_authorized(self) -> bool:
        return False

    @property
    def action_authorized(self) -> bool:
        return False


@dataclass(frozen=True, slots=True)
class MemoryRowDeltaReview:
    retained_rows: int
    current_rows: int
    appended_events: int
    explained_changes: int
    review_sha256: str

    @property
    def writer_authenticated(self) -> bool:
        return False

    @property
    def disclosure_authorized(self) -> bool:
        return False

    @property
    def action_authorized(self) -> bool:
        return False


_WITNESS = MemoryRowDeltaWitness
_REPORT = MemoryRowDeltaReview
_STORE = SQLiteMemoryStore


def _commitment(row: sqlite3.Row) -> tuple[str, int, str]:
    record = _record(row)
    payload = (
        record.memory_id, record.scope.owner_id, record.scope.namespace,
        record.source_id, record.revision, record.content_sha256,
        hashlib.sha256(row["metadata_json"].encode("utf-8")).hexdigest(),
        record.created_at_ms, record.updated_at_ms, record.expires_at_ms,
    )
    encoded = json.dumps(payload, ensure_ascii=True, separators=(",", ":")).encode("ascii")
    return record.memory_id, record.revision, hashlib.sha256(_DOMAIN + encoded).hexdigest()


def _scan(store: SQLiteMemoryStore) -> tuple[
    tuple[tuple[str, int, str], ...],
    tuple[tuple[object, ...], ...],
]:
    path = store.path
    try:
        with closing(store._connect_readonly()) as conn:
            if store.path is not path:
                raise MemoryRowDeltaRejected("Memory source retargeted")
            conn.execute("BEGIN")
            try:
                _validate_v1_schema(conn)
                rows = []
                for row in conn.execute("SELECT * FROM memories ORDER BY memory_id"):
                    if len(rows) >= _MAX_ROWS:
                        raise MemoryRowDeltaRejected("row scan budget exceeded")
                    rows.append(_commitment(row))
                    if store.path is not path:
                        raise MemoryRowDeltaRejected("Memory source retargeted")
                events = []
                previous_id = 0
                for entry in conn.execute(
                    "SELECT event_id,memory_id,owner_id,namespace,operation,"
                    "revision,occurred_at_ms FROM memory_events ORDER BY event_id"
                ):
                    if len(events) >= _MAX_EVENTS:
                        raise MemoryRowDeltaRejected("event scan budget exceeded")
                    event_id, memory_id, owner, namespace, operation, revision, at = entry
                    if (
                        type(event_id) is not int
                        or not previous_id < event_id
                        or type(memory_id) is not str
                        or prefix._ID.fullmatch(memory_id) is None
                        or type(operation) is not str
                        or operation not in prefix._OPERATIONS
                        or type(revision) is not int
                        or not 1 <= revision <= (1 << 63) - 1
                        or type(at) is not int
                        or not 0 <= at <= (1 << 63) - 1
                        or type(owner) is not str
                        or type(namespace) is not str
                    ):
                        raise MemoryRowDeltaRejected("invalid persisted event")
                    events.append(tuple(entry))
                    previous_id = event_id
                    if store.path is not path:
                        raise MemoryRowDeltaRejected("Memory source retargeted")
                conn.rollback()
            except BaseException:
                conn.rollback()
                raise
    except sqlite3.Error as exc:
        raise MemoryRowDeltaRejected("read-only Memory snapshot unavailable") from exc
    if store.path is not path:
        raise MemoryRowDeltaRejected("Memory source retargeted")
    return tuple(rows), tuple(events)


def _prefix_hash(events: tuple[tuple[object, ...], ...], count: int) -> str:
    state = hashlib.sha256(prefix._DOMAIN)
    for entry in events[:count]:
        prefix._charge(state, entry)
    return state.hexdigest()


def _validate(value: MemoryRowDeltaWitness) -> tuple[object, ...]:
    if type(value) is not _WITNESS:
        raise MemoryRowDeltaRejected("exact retained Memory row witness required")
    epoch = (
        value.event_count, value.last_event_id,
        value.event_prefix_sha256, value.rows,
    )
    count, last_id, root, rows = epoch
    if (
        type(count) is not int or not 0 <= count <= _MAX_EVENTS
        or type(last_id) is not int or not 0 <= last_id <= (1 << 63) - 1
        or (count == 0 and last_id != 0)
        or (count > 0 and last_id < count)
        or type(root) is not str or prefix._SHA.fullmatch(root) is None
        or type(rows) is not tuple or len(rows) > _MAX_ROWS
        or value.independently_authenticated is not False
        or value.historical_writer_authenticated is not False
        or value.disclosure_authorized is not False
        or value.action_authorized is not False
    ):
        raise MemoryRowDeltaRejected("invalid retained Memory row witness")
    previous = ""
    for item in rows:
        if (
            type(item) is not tuple or len(item) != 3
            or type(item[0]) is not str or prefix._ID.fullmatch(item[0]) is None
            or item[0] <= previous
            or type(item[1]) is not int or not 1 <= item[1] <= (1 << 63) - 1
            or type(item[2]) is not str or prefix._SHA.fullmatch(item[2]) is None
        ):
            raise MemoryRowDeltaRejected("invalid retained row commitment")
        previous = item[0]
    return epoch


def capture_local_memory_row_delta(store: SQLiteMemoryStore) -> MemoryRowDeltaWitness:
    """Capture hashes, revisions and local event prefix, never private text."""
    if type(store) is not _STORE:
        raise MemoryRowDeltaRejected("exact Memory source required")
    rows, events = _scan(store)
    root = _prefix_hash(events, len(events))
    result = _WITNESS(len(events), events[-1][0] if events else 0, root, rows)
    _validate(result)
    return result


def review_retained_memory_row_delta(
    store: SQLiteMemoryStore, retained: MemoryRowDeltaWitness,
) -> MemoryRowDeltaReview:
    """Require a matching prior event prefix and event-backed row changes."""
    if type(store) is not _STORE:
        raise MemoryRowDeltaRejected("exact Memory source required")
    epoch = _validate(retained)
    source = store.path

    def stable() -> None:
        if store.path is not source or any(
            actual is not original for actual, original in zip(
                _validate(retained), epoch, strict=True,
            )
        ):
            raise MemoryRowDeltaRejected("retained row witness changed during scan")

    stable()
    rows, events = _scan(store)
    stable()
    old_count, old_tail, old_root, old_rows = epoch
    if (
        len(events) < old_count
        or (old_count and events[old_count - 1][0] != old_tail)
        or _prefix_hash(events, old_count) != old_root
    ):
        raise MemoryRowDeltaRejected("retained event prefix changed or rolled back")
    changed_ids = {entry[1] for entry in events[old_count:]}
    before = {item[0]: item for item in old_rows}
    current = {item[0]: item for item in rows}
    changes = 0
    for identifier in before.keys() | current.keys():
        if before.get(identifier) != current.get(identifier):
            if identifier not in changed_ids:
                raise MemoryRowDeltaRejected(
                    "Memory row changed without its own appended event"
                )
            changes += 1
    encoded = json.dumps(
        (epoch[:3], len(old_rows), len(rows), len(events), changes),
        separators=(",", ":"), ensure_ascii=True,
    ).encode("ascii")
    root = hashlib.sha256(_DOMAIN + encoded).hexdigest()
    stable()
    report = _REPORT(len(old_rows), len(rows), len(events) - old_count, changes, root)
    if (
        type(report) is not _REPORT
        or report.retained_rows != len(old_rows)
        or report.current_rows != len(rows)
        or report.appended_events != len(events) - old_count
        or report.explained_changes != changes
        or report.review_sha256 is not root
        or report.writer_authenticated is not False
        or report.disclosure_authorized is not False
        or report.action_authorized is not False
    ):
        raise MemoryRowDeltaRejected("Memory row review gained authority")
    stable()
    return report
