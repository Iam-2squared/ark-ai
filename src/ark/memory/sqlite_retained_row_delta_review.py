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
from .contracts import MemorySchemaError, MemoryScope
from .sqlite_store import SQLiteMemoryStore, _record, _validate_v1_schema

_MAX_ROWS = 10_000
_MAX_EVENTS = 40_000
_DOMAIN = b"ARK-retained-memory-row-delta-v1\0"
_REVIEW_DOMAIN = b"ARK-retained-memory-row-delta-review-v2\0"

# Private row metadata is serialized and hashed during detached review.
# Refuse substituted codec/digest code before reading it from SQLite.
_ORIGINAL_HASHLIB = hashlib
_ORIGINAL_SHA256 = hashlib.sha256
_ORIGINAL_JSON = json
_ORIGINAL_DUMPS = json.dumps
_ORIGINAL_DOMAIN = _DOMAIN
_ORIGINAL_REVIEW_DOMAIN = _REVIEW_DOMAIN


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
_WITNESS_FIELDS = ("event_count", "last_event_id", "event_prefix_sha256", "rows")
_REPORT_FIELDS = (
    "retained_rows", "current_rows", "appended_events",
    "explained_changes", "review_sha256",
)
_CARRIER_HOOKS = ("__init__", "__new__", "__getattribute__", "__getattr__")
_ORIGINAL_WITNESS_CARRIERS = tuple(
    vars(_WITNESS).get(name) for name in (*_WITNESS_FIELDS, *_CARRIER_HOOKS)
)
_ORIGINAL_REPORT_CARRIERS = tuple(
    vars(_REPORT).get(name) for name in (*_REPORT_FIELDS, *_CARRIER_HOOKS)
)


def _require_original_carriers() -> None:
    # A frozen witness/report may still run injected slot descriptors or
    # constructors. Reject substitutions before reading private SQLite rows
    # or evaluating the first caller-held retained witness field.
    if (
        MemoryRowDeltaWitness is not _WITNESS
        or MemoryRowDeltaReview is not _REPORT
        or any(
            vars(_WITNESS).get(name) is not original
            for name, original in zip(
                (*_WITNESS_FIELDS, *_CARRIER_HOOKS),
                _ORIGINAL_WITNESS_CARRIERS, strict=True,
            )
        )
        or any(
            vars(_REPORT).get(name) is not original
            for name, original in zip(
                (*_REPORT_FIELDS, *_CARRIER_HOOKS),
                _ORIGINAL_REPORT_CARRIERS, strict=True,
            )
        )
    ):
        raise MemoryRowDeltaRejected("retained Memory row carrier descriptors changed")


def _require_original_row_delta_digest() -> None:
    if (
        hashlib is not _ORIGINAL_HASHLIB
        or hashlib.sha256 is not _ORIGINAL_SHA256
        or json is not _ORIGINAL_JSON
        or json.dumps is not _ORIGINAL_DUMPS
        or _DOMAIN is not _ORIGINAL_DOMAIN
        or _REVIEW_DOMAIN is not _ORIGINAL_REVIEW_DOMAIN
    ):
        raise MemoryRowDeltaRejected("Memory row digest dependencies changed")


def _commitment(row: sqlite3.Row) -> tuple[str, int, str]:
    _require_original_row_delta_digest()
    record = _record(row)
    _require_original_row_delta_digest()
    payload = (
        record.memory_id, record.scope.owner_id, record.scope.namespace,
        record.source_id, record.revision, record.content_sha256,
        hashlib.sha256(row["metadata_json"].encode("utf-8")).hexdigest(),
        record.created_at_ms, record.updated_at_ms, record.expires_at_ms,
    )
    _require_original_row_delta_digest()
    encoded = json.dumps(payload, ensure_ascii=True, separators=(",", ":")).encode("ascii")
    _require_original_row_delta_digest()
    digest = hashlib.sha256(_DOMAIN + encoded).hexdigest()
    _require_original_row_delta_digest()
    return record.memory_id, record.revision, digest


def _scan(store: SQLiteMemoryStore) -> tuple[
    tuple[tuple[str, int, str], ...],
    tuple[tuple[object, ...], ...],
]:
    _require_original_row_delta_digest()
    path = store.path
    try:
        with closing(store._connect_readonly()) as conn:
            if store.path is not path:
                raise MemoryRowDeltaRejected("Memory source retargeted")
            conn.execute("BEGIN")
            try:
                _validate_v1_schema(conn)
                rows = []
                current: dict[str, tuple[str, str, int, int, int]] = {}
                for row in conn.execute("SELECT * FROM memories ORDER BY memory_id"):
                    if len(rows) >= _MAX_ROWS:
                        raise MemoryRowDeltaRejected("row scan budget exceeded")
                    commitment = _commitment(row)
                    rows.append(commitment)
                    current[commitment[0]] = (
                        row["owner_id"], row["namespace"], commitment[1],
                        row["created_at_ms"], row["updated_at_ms"],
                    )
                    if store.path is not path:
                        raise MemoryRowDeltaRejected("Memory source retargeted")
                events = []
                lifecycle: dict[str, tuple[str, str, int, bool, int, int]] = {}
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
                        or event_id != previous_id + 1
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
                    # Unlike a mere old-prefix comparison, an independent
                    # row snapshot must also reconcile the CURRENT lifecycle.
                    # No synthetic appended event can excuse a revision,
                    # scope or active/deleted mismatch of the live row.
                    try:
                        MemoryScope(owner, namespace)
                    except (TypeError, ValueError) as exc:
                        raise MemoryRowDeltaRejected(
                            "invalid persisted event scope"
                        ) from exc
                    previous = lifecycle.get(memory_id)
                    if previous is not None and previous[:2] != (owner, namespace):
                        raise MemoryRowDeltaRejected("Memory event scope changed")
                    if previous is not None and at < previous[5]:
                        raise MemoryRowDeltaRejected("Memory event clock regressed")
                    if operation == "create":
                        if revision != 1 or previous is not None and previous[3]:
                            raise MemoryRowDeltaRejected(
                                "invalid Memory event creation lifecycle"
                            )
                        active = True
                        created_at = at
                    else:
                        if previous is None or not previous[3]:
                            raise MemoryRowDeltaRejected(
                                "Memory event lacks active predecessor"
                            )
                        wanted = previous[2] + (operation == "update")
                        if revision != wanted:
                            raise MemoryRowDeltaRejected(
                                "Memory event revision lifecycle mismatch"
                            )
                        active = operation == "update"
                        created_at = previous[4]
                    lifecycle[memory_id] = (
                        owner, namespace, revision, active, created_at, at,
                    )
                    events.append(tuple(entry))
                    previous_id = event_id
                    if store.path is not path:
                        raise MemoryRowDeltaRejected("Memory source retargeted")
                for identifier, state in lifecycle.items():
                    observed = current.pop(identifier, None)
                    if state[3] and observed != (
                        state[0], state[1], state[2], state[4], state[5],
                    ):
                        raise MemoryRowDeltaRejected(
                            "live Memory row or timestamps differ from event lifecycle"
                        )
                    if not state[3] and observed is not None:
                        raise MemoryRowDeltaRejected(
                            "terminal Memory event left a live row"
                        )
                if current:
                    raise MemoryRowDeltaRejected(
                        "live Memory row lacks creation event"
                    )
                # Event IDs are global AUTOINCREMENT; a complete local
                # snapshot must not accept a removed final append when its
                # live row was also erased. This local high-water mark cannot
                # attest a deliberately rewritten sqlite_sequence or an
                # independent writer, so retained external custody is still
                # required.
                sequences = conn.execute(
                    "SELECT seq FROM sqlite_sequence WHERE name='memory_events'"
                ).fetchall()
                if (
                    (not events and sequences)
                    or (events and (
                        len(sequences) != 1
                        or type(sequences[0][0]) is not int
                        or sequences[0][0] != previous_id
                    ))
                ):
                    raise MemoryRowDeltaRejected(
                        "Memory append-only event high-water mark differs"
                    )
                conn.rollback()
            except BaseException:
                conn.rollback()
                raise
    except MemoryRowDeltaRejected:
        raise
    except MemorySchemaError as exc:
        raise MemoryRowDeltaRejected("Memory row or schema integrity unavailable") from exc
    except sqlite3.Error as exc:
        raise MemoryRowDeltaRejected("read-only Memory snapshot unavailable") from exc
    if store.path is not path:
        raise MemoryRowDeltaRejected("Memory source retargeted")
    return tuple(rows), tuple(events)


def _prefix_hash(events: tuple[tuple[object, ...], ...], count: int) -> str:
    _require_original_row_delta_digest()
    state = hashlib.sha256(prefix._DOMAIN)
    for entry in events[:count]:
        _require_original_row_delta_digest()
        prefix._charge(state, entry)
    _require_original_row_delta_digest()
    return state.hexdigest()


def _validate(value: MemoryRowDeltaWitness) -> tuple[object, ...]:
    _require_original_carriers()
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
    _require_original_row_delta_digest()
    if type(store) is not _STORE:
        raise MemoryRowDeltaRejected("exact Memory source required")
    _require_original_carriers()
    rows, events = _scan(store)
    root = _prefix_hash(events, len(events))
    _require_original_carriers()
    result = _WITNESS(len(events), events[-1][0] if events else 0, root, rows)
    denial_fields = (
        "independently_authenticated", "historical_writer_authenticated",
        "disclosure_authorized", "action_authorized",
    )
    denial_descriptors = tuple(vars(_WITNESS)[name] for name in denial_fields)
    pinned = _validate(result)
    # Even a False-valued final getter can reflectively replace a frozen
    # witness field or an earlier denial property. A local capture must never
    # return that altered baseline as independently authenticated evidence.
    if any(
        now is not original for now, original in zip((
            result.event_count, result.last_event_id,
            result.event_prefix_sha256, result.rows,
        ), pinned, strict=True)
    ):
        raise MemoryRowDeltaRejected("captured row witness changed after denial")
    if any(
        vars(_WITNESS).get(name) is not original
        for name, original in zip(denial_fields, denial_descriptors, strict=True)
    ):
        raise MemoryRowDeltaRejected(
            "captured row witness authority descriptor changed"
        )
    return result


def review_retained_memory_row_delta(
    store: SQLiteMemoryStore, retained: MemoryRowDeltaWitness,
) -> MemoryRowDeltaReview:
    """Require a matching prior event prefix and event-backed row changes."""
    _require_original_row_delta_digest()
    if type(store) is not _STORE:
        raise MemoryRowDeltaRejected("exact Memory source required")
    _require_original_carriers()
    epoch = _validate(retained)
    source = store.path

    def stable() -> None:
        _require_original_row_delta_digest()
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
    # A count-only review digest can collide for two valid sibling event
    # tails with identical counts but different row contents or timestamps.
    # Bind the *actual* live row commitments, retained baseline and complete
    # verified event chain. Retained witnesses remain compatible (v1 rows).
    full_event_root = _prefix_hash(events, len(events))
    stable()
    encoded = json.dumps(
        (epoch, old_rows, rows, len(events) - old_count,
         full_event_root, tuple(sorted(changed_ids)), changes),
        separators=(",", ":"), ensure_ascii=True,
    ).encode("ascii")
    _require_original_row_delta_digest()
    root = hashlib.sha256(_REVIEW_DOMAIN + encoded).hexdigest()
    stable()
    _require_original_carriers()
    report = _REPORT(len(old_rows), len(rows), len(events) - old_count, changes, root)

    def report_stable() -> None:
        _require_original_carriers()
        if (
            type(report) is not _REPORT
            or type(report.retained_rows) is not int
            or report.retained_rows != len(old_rows)
            or type(report.current_rows) is not int
            or report.current_rows != len(rows)
            or type(report.appended_events) is not int
            or report.appended_events != len(events) - old_count
            or type(report.explained_changes) is not int
            or report.explained_changes != changes
            or type(report.review_sha256) is not str
            or report.review_sha256 is not root
            or report.writer_authenticated is not False
            or report.disclosure_authorized is not False
            or report.action_authorized is not False
        ):
            raise MemoryRowDeltaRejected("Memory row review gained authority or changed")

    report_stable()
    stable()
    # Authority properties are callbacks. Their final False return can still
    # rewrite an earlier field or flag, even with frozen dataclass instances.
    report_stable()
    stable()
    if (
        type(report) is not _REPORT
        or type(report.retained_rows) is not int
        or report.retained_rows != len(old_rows)
        or type(report.current_rows) is not int
        or report.current_rows != len(rows)
        or type(report.appended_events) is not int
        or report.appended_events != len(events) - old_count
        or type(report.explained_changes) is not int
        or report.explained_changes != changes
        or type(report.review_sha256) is not str
        or report.review_sha256 is not root
    ):
        raise MemoryRowDeltaRejected("Memory row report changed after final denial")
    return report
