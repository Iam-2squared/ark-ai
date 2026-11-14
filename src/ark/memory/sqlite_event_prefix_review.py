"""Read-only retained event-prefix comparison for local Memory v1 history.

A caller must retain the first witness outside this SQLite database. If later
events are appended, recompute the ORIGINAL event prefix in the SAME read
transaction as the current tail. This detects local historical rewrites that
a full current-state digest alone would classify merely as a new tail.

This is an event-only continuity check: it does NOT reconcile live Memory rows,
authenticate the writer/witness, prove erasure/consent, or grant any access.
"""

from __future__ import annotations

import hashlib
import json
import re
import sqlite3
from contextlib import closing
from dataclasses import dataclass

from .contracts import MemorySchemaError, MemoryScope
from .sqlite_store import SQLITE_INT_MAX, SQLiteMemoryStore, _validate_v1_schema

_MAX_EVENTS = 40_000
_ID = re.compile(r"mem_[0-9a-f]{64}\Z")
_SHA = re.compile(r"[0-9a-f]{64}\Z")
_OPERATIONS = frozenset(("create", "update", "delete", "expire"))
_DOMAIN = b"ARK-memory-retained-event-prefix-v1\0"
_COMPARISON_DOMAIN = b"ARK-memory-retained-event-prefix-comparison-v1\0"


class MemoryEventPrefixRejected(MemorySchemaError):
    """A retained event prefix cannot match bounded local SQLite history."""


@dataclass(frozen=True, slots=True)
class MemoryEventPrefixWitness:
    event_count: int
    last_event_id: int
    prefix_sha256: str

    @property
    def independently_authenticated(self) -> bool:
        return False

    @property
    def historical_writer_authenticated(self) -> bool:
        return False

    @property
    def memory_disclosure_authorized(self) -> bool:
        return False

    @property
    def action_authorized(self) -> bool:
        return False


@dataclass(frozen=True, slots=True)
class MemoryEventPrefixComparison:
    previous_event_count: int
    current_event_count: int
    status: str
    comparison_sha256: str

    @property
    def historical_writer_authenticated(self) -> bool:
        return False

    @property
    def independent_witness_custody_proven(self) -> bool:
        return False

    @property
    def memory_disclosure_authorized(self) -> bool:
        return False

    @property
    def action_authorized(self) -> bool:
        return False


_WITNESS = MemoryEventPrefixWitness
_COMPARISON = MemoryEventPrefixComparison
_STORE = SQLiteMemoryStore
_WITNESS_DENIALS = (
    "independently_authenticated", "historical_writer_authenticated",
    "memory_disclosure_authorized", "action_authorized",
)
_COMPARISON_DENIALS = (
    "historical_writer_authenticated", "independent_witness_custody_proven",
    "memory_disclosure_authorized", "action_authorized",
)
_WITNESS_FIELDS = ("event_count", "last_event_id", "prefix_sha256")
_COMPARISON_FIELDS = (
    "previous_event_count", "current_event_count", "status",
    "comparison_sha256",
)
_CARRIER_HOOKS = ("__new__", "__getattribute__", "__getattr__")
_WITNESS_ORIGINAL_FIELDS = tuple(vars(_WITNESS)[name] for name in _WITNESS_FIELDS)
_COMPARISON_ORIGINAL_FIELDS = tuple(
    vars(_COMPARISON)[name] for name in _COMPARISON_FIELDS
)
_WITNESS_ORIGINAL_HOOKS = tuple(
    vars(_WITNESS).get(name) for name in _CARRIER_HOOKS
)
_COMPARISON_ORIGINAL_HOOKS = tuple(
    vars(_COMPARISON).get(name) for name in _CARRIER_HOOKS
)
_WITNESS_ORIGINAL_INIT = vars(_WITNESS)["__init__"]
_COMPARISON_ORIGINAL_INIT = vars(_COMPARISON)["__init__"]
_WITNESS_ORIGINAL_FLAGS = tuple(vars(_WITNESS)[name] for name in _WITNESS_DENIALS)
_COMPARISON_ORIGINAL_FLAGS = tuple(
    vars(_COMPARISON)[name] for name in _COMPARISON_DENIALS
)


# Keep v1 local event grammar, bounded scan size, and digest separation
# immutable within this optional, read-only observer. This is not an
# authenticated append log or independent witness; it only prevents
# caller-rebound local parser constants from silently expanding acceptance.
_ORIGINAL_ID = _ID
_ORIGINAL_SHA = _SHA
_ORIGINAL_OPERATIONS = _OPERATIONS
_ORIGINAL_MAX_EVENTS = _MAX_EVENTS
_ORIGINAL_DOMAIN = _DOMAIN
_ORIGINAL_COMPARISON_DOMAIN = _COMPARISON_DOMAIN


def _require_original_prefix_protocol() -> None:
    if (
        _ID is not _ORIGINAL_ID
        or _SHA is not _ORIGINAL_SHA
        or _OPERATIONS is not _ORIGINAL_OPERATIONS
        or _MAX_EVENTS is not _ORIGINAL_MAX_EVENTS
        or _DOMAIN is not _ORIGINAL_DOMAIN
        or _COMPARISON_DOMAIN is not _ORIGINAL_COMPARISON_DOMAIN
    ):
        raise MemoryEventPrefixRejected("local event prefix protocol changed")


def _original_witness_flags() -> None:
    if (
        MemoryEventPrefixWitness is not _WITNESS
        or vars(_WITNESS).get("__init__") is not _WITNESS_ORIGINAL_INIT
        or any(
            vars(_WITNESS).get(name) is not original
            for name, original in zip(
                _WITNESS_FIELDS, _WITNESS_ORIGINAL_FIELDS, strict=True,
            )
        )
        or any(
            vars(_WITNESS).get(name) is not original
            for name, original in zip(
                _CARRIER_HOOKS, _WITNESS_ORIGINAL_HOOKS, strict=True,
            )
        )
        or any(
            vars(_WITNESS).get(name) is not descriptor
            for name, descriptor in zip(
                _WITNESS_DENIALS, _WITNESS_ORIGINAL_FLAGS, strict=True,
            )
        )
    ):
        raise MemoryEventPrefixRejected("retained event witness authority changed")


def _original_comparison_flags() -> None:
    if (
        MemoryEventPrefixComparison is not _COMPARISON
        or vars(_COMPARISON).get("__init__") is not _COMPARISON_ORIGINAL_INIT
        or any(
            vars(_COMPARISON).get(name) is not original
            for name, original in zip(
                _COMPARISON_FIELDS, _COMPARISON_ORIGINAL_FIELDS, strict=True,
            )
        )
        or any(
            vars(_COMPARISON).get(name) is not original
            for name, original in zip(
                _CARRIER_HOOKS, _COMPARISON_ORIGINAL_HOOKS, strict=True,
            )
        )
        or any(
            vars(_COMPARISON).get(name) is not descriptor
            for name, descriptor in zip(
                _COMPARISON_DENIALS, _COMPARISON_ORIGINAL_FLAGS, strict=True,
            )
        )
    ):
        raise MemoryEventPrefixRejected("event prefix comparison authority changed")


def _witness_epoch(value: object) -> tuple[object, ...]:
    if type(value) is not _WITNESS:
        raise MemoryEventPrefixRejected("exact retained event witness required")
    # Descriptor reads can execute caller-installed code. Check the original
    # class before touching any retained witness slot, not only at the
    # later deny-only property checks.
    _original_witness_flags()
    fields = (value.event_count, value.last_event_id, value.prefix_sha256)
    count, tail, digest = fields
    if (
        type(count) is not int or not 0 <= count <= _MAX_EVENTS
        or type(tail) is not int or not 0 <= tail <= SQLITE_INT_MAX
        # This v1 journal uses dense AUTOINCREMENT IDs from genesis.
        # A retained tip with tail > count is noncanonical even if its
        # caller supplies a syntactically valid digest. Refuse it before I/O.
        or tail != count
        or type(digest) is not str or _SHA.fullmatch(digest) is None
    ):
        raise MemoryEventPrefixRejected("invalid event prefix shape or authority")
    for name in _WITNESS_DENIALS:
        # Verify the original class descriptor before any getter is invoked.
        # Synthetic callbacks can install a False-valued executable getter.
        _original_witness_flags()
        if getattr(value, name) is not False:
            raise MemoryEventPrefixRejected("invalid event prefix authority")
        _original_witness_flags()
    _original_witness_flags()
    return fields


def _charge(hasher: object, event: tuple[object, ...]) -> None:
    hasher.update(
        json.dumps(event, separators=(",", ":"), ensure_ascii=True).encode("ascii")
        + b"\n"
    )


def _scan(
    store: SQLiteMemoryStore, *, prefix_count: int | None,
) -> tuple[MemoryEventPrefixWitness, tuple[int, str] | None]:
    _require_original_prefix_protocol()
    if type(store) is not _STORE:
        raise MemoryEventPrefixRejected("exact local Memory store required")
    source_path = store.path

    def stable_source() -> None:
        _require_original_prefix_protocol()
        if type(store) is not _STORE or store.path is not source_path:
            raise MemoryEventPrefixRejected("local Memory source changed during prefix read")

    full = hashlib.sha256(_DOMAIN)
    prefix = hashlib.sha256(_DOMAIN)
    history: dict[str, tuple[str, str, int, bool]] = {}
    count = 0
    last = 0
    prefix_tail = 0
    stable_source()
    try:
        with closing(store._connect_readonly()) as conn:
            stable_source()
            conn.execute("BEGIN")
            try:
                _validate_v1_schema(conn)
                stable_source()
                for event in conn.execute(
                    "SELECT event_id,memory_id,owner_id,namespace,operation,"
                    "revision,occurred_at_ms FROM memory_events ORDER BY event_id"
                ):
                    count += 1
                    if count > _MAX_EVENTS:
                        raise MemoryEventPrefixRejected("event prefix scan budget exceeded")
                    event_id, memory_id, owner, namespace, operation, revision, at = event
                    if (
                        type(event_id) is not int or not last < event_id <= SQLITE_INT_MAX
                        or type(memory_id) is not str or _ID.fullmatch(memory_id) is None
                        or type(operation) is not str or operation not in _OPERATIONS
                        or type(revision) is not int
                        or not 1 <= revision <= SQLITE_INT_MAX
                        or type(at) is not int or not 0 <= at <= SQLITE_INT_MAX
                    ):
                        raise MemoryEventPrefixRejected("invalid stored event prefix row")
                    # The v1 event journal has no compaction/deletion API.
                    # A missing genesis/middle ID must not pass even when
                    # the independently retained prefix predates the gap.
                    if event_id != last + 1:
                        raise MemoryEventPrefixRejected(
                            "Memory event ID gap in append-only prefix history"
                        )
                    try:
                        MemoryScope(owner, namespace)
                    except (TypeError, ValueError) as exc:
                        raise MemoryEventPrefixRejected("invalid stored event scope") from exc
                    previous = history.get(memory_id)
                    if previous is not None and previous[:2] != (owner, namespace):
                        raise MemoryEventPrefixRejected("event identity changed scope")
                    if operation == "create":
                        if revision != 1 or previous is not None and previous[3]:
                            raise MemoryEventPrefixRejected("invalid event creation lifecycle")
                        active = True
                    else:
                        if previous is None or not previous[3]:
                            raise MemoryEventPrefixRejected("event lacks active lifecycle")
                        wanted = previous[2] + (operation == "update")
                        if revision != wanted:
                            raise MemoryEventPrefixRejected("invalid event revision lifecycle")
                        active = operation == "update"
                    history[memory_id] = (owner, namespace, revision, active)
                    fields = (
                        event_id, memory_id, owner, namespace, operation, revision, at,
                    )
                    _charge(full, fields)
                    if prefix_count is not None and count <= prefix_count:
                        _charge(prefix, fields)
                        prefix_tail = event_id
                    last = event_id
                    stable_source()
                # A prefix alone cannot prove historical custody, but local
                # AUTOINCREMENT state must agree with the complete event
                # stream. Otherwise deleting the latest event (and possibly
                # its row) can look like a valid earlier prefix. This is a
                # read-only consistency check in the SAME snapshot.
                sequences = conn.execute(
                    "SELECT seq FROM sqlite_sequence WHERE name='memory_events'"
                ).fetchall()
                if (
                    (count == 0 and sequences)
                    or (count > 0 and (
                        len(sequences) != 1
                        or type(sequences[0][0]) is not int
                        or sequences[0][0] != last
                    ))
                ):
                    raise MemoryEventPrefixRejected(
                        "Memory event append high-water mark differs"
                    )
                stable_source()
                conn.commit()
            except BaseException:
                conn.rollback()
                raise
    except sqlite3.Error as exc:
        raise MemoryEventPrefixRejected("local Memory event prefix unavailable") from exc
    stable_source()
    # Constructor custody is checked before invoking untrusted replacement
    # code, including mutations performed by a reentrant event hash callback.
    _original_witness_flags()
    witness = _WITNESS(count, last, full.hexdigest())
    if _witness_epoch(witness) != (count, last, full.hexdigest()):
        raise MemoryEventPrefixRejected("local event witness changed after scan")
    if prefix_count is None:
        return witness, None
    if prefix_count > count:
        raise MemoryEventPrefixRejected("retained event history rolled back")
    return witness, (prefix_tail, prefix.hexdigest())


def capture_local_memory_event_prefix(
    store: SQLiteMemoryStore,
) -> MemoryEventPrefixWitness:
    """Capture an inert local event-history tip; caller protects its custody."""
    witness, _ = _scan(store, prefix_count=None)
    return witness


def compare_local_memory_event_prefix(
    store: SQLiteMemoryStore,
    retained: MemoryEventPrefixWitness,
) -> MemoryEventPrefixComparison:
    """Check the old event prefix even when a newer local event tail exists."""
    _require_original_prefix_protocol()
    old = _witness_epoch(retained)

    def stable_retained() -> None:
        _require_original_prefix_protocol()
        if any(
            value is not pinned for value, pinned in zip(
                _witness_epoch(retained), old, strict=True,
            )
        ):
            raise MemoryEventPrefixRejected("retained event prefix carrier changed")

    stable_retained()
    current, prefix = _scan(store, prefix_count=old[0])
    stable_retained()
    if prefix is None or prefix != (old[1], old[2]):
        raise MemoryEventPrefixRejected("retained event prefix changed or rolled back")
    status = (
        "ADVANCED_PREFIX_UNAUTHENTICATED"
        if current.event_count > old[0] else "UNCHANGED_LOCAL_EVENT_PREFIX"
    )
    payload = json.dumps(
        (old, _witness_epoch(current), status),
        ensure_ascii=True, separators=(",", ":"),
    ).encode("ascii")
    stable_retained()
    digest = hashlib.sha256(_COMPARISON_DOMAIN + payload).hexdigest()
    # The digest callback is another injection epoch: reject substituted
    # result constructors before they can execute.
    _original_comparison_flags()
    result = _COMPARISON(old[0], current.event_count, status, digest)
    # An injected constructor can rebind a field after the preceding check.
    # Refuse it before reading any return carrier attribute.
    _original_comparison_flags()
    if (
        type(result) is not _COMPARISON
        or type(result.previous_event_count) is not int
        or result.previous_event_count != old[0]
        or type(result.current_event_count) is not int
        or result.current_event_count != current.event_count
        or result.status is not status
        or result.comparison_sha256 is not digest
    ):
        raise MemoryEventPrefixRejected("event prefix comparison acquired authority")
    for name in _COMPARISON_DENIALS:
        _original_comparison_flags()
        if getattr(result, name) is not False:
            raise MemoryEventPrefixRejected("event prefix comparison acquired authority")
        _original_comparison_flags()
        stable_retained()
    _original_comparison_flags()
    stable_retained()
    return result
