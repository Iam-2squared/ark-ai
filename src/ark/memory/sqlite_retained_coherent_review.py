"""One-transaction retained event-prefix AND live-row reconciliation.

This offline, read-only reviewer deliberately runs the retained event-prefix
comparison and complete v1 row/event lifecycle audit inside ONE SQLite
snapshot. Two independent read calls cannot make that same claim if a writer
commits between their snapshots. The retained witness is caller-supplied and
is NOT independently authenticated. An appended event tail is not permission
to disclose, execute, or assert historical writer provenance.
"""

from __future__ import annotations

import hashlib
import json
import sqlite3
from contextlib import closing
from dataclasses import dataclass

from . import sqlite_alignment_retained_review as retained_alignment
from . import sqlite_event_alignment as alignment
from . import sqlite_event_prefix_review as prefix
from . import sqlite_retained_row_delta_review as row_delta
from .contracts import MemorySchemaError, MemoryScope
from .sqlite_store import SQLITE_INT_MAX, SQLiteMemoryStore, _record, _validate_v1_schema

_MAX_ROWS = 10_000
_MAX_EVENTS = 40_000
_RESULT_DOMAIN = b"ARK-memory-retained-coherent-snapshot-v1\0"
# Prevent replacement of digest/serialization dependencies while traversing
# an untrusted local WAL snapshot. This is process-local callback custody,
# never authenticated history or permission to disclose.
_ORIGINAL_HASHLIB = hashlib
_ORIGINAL_JSON = json
_ORIGINAL_SHA256 = hashlib.sha256
_ORIGINAL_JSON_DUMPS = json.dumps
_ORIGINAL_RESULT_DOMAIN = _RESULT_DOMAIN


class MemoryCoherentHistoryRejected(MemorySchemaError):
    """Local retained prefix and current row/event snapshot cannot agree."""


@dataclass(frozen=True, slots=True)
class RetainedCoherentMemoryReview:
    previous_event_count: int
    current_event_count: int
    row_count: int
    scope_count: int
    last_event_id: int
    status: str
    current_alignment_sha256: str
    current_event_sha256: str
    review_sha256: str
    # True only when a separately retained per-row witness was reconciled
    # inside this same SQLite transaction; NOT authenticated writer evidence.
    retained_row_delta_checked: bool = False

    @property
    def independently_authenticated(self) -> bool:
        return False

    @property
    def historical_writer_authenticated(self) -> bool:
        return False

    @property
    def consent_verified(self) -> bool:
        return False

    @property
    def memory_disclosure_authorized(self) -> bool:
        return False

    @property
    def action_authorized(self) -> bool:
        return False

    @property
    def cross_store_atomicity_proven(self) -> bool:
        return False


_RESULT = RetainedCoherentMemoryReview
_STORE = SQLiteMemoryStore
# Result objects are frozen but their class descriptors and constructors can
# still be replaced at runtime. Do not run a substituted getter/initializer
# even if it would return False: validate before reading private rows, at
# reentrant hash/SQLite boundaries and before constructing the final receipt.
_RESULT_FIELDS = (
    "previous_event_count", "current_event_count", "row_count",
    "scope_count", "last_event_id", "status",
    "current_alignment_sha256", "current_event_sha256", "review_sha256",
    "retained_row_delta_checked",
)
_RESULT_DENIALS = (
    "independently_authenticated", "historical_writer_authenticated",
    "consent_verified", "memory_disclosure_authorized",
    "action_authorized", "cross_store_atomicity_proven",
)
_RESULT_HOOKS = ("__init__", "__new__", "__getattribute__", "__getattr__")
_ORIGINAL_RESULT_FIELDS = tuple(vars(_RESULT)[name] for name in _RESULT_FIELDS)
_ORIGINAL_RESULT_DENIALS = tuple(vars(_RESULT)[name] for name in _RESULT_DENIALS)
_ORIGINAL_RESULT_HOOKS = tuple(vars(_RESULT).get(name) for name in _RESULT_HOOKS)


def _require_original_result_carrier() -> None:
    if (
        hashlib is not _ORIGINAL_HASHLIB
        or json is not _ORIGINAL_JSON
        or hashlib.sha256 is not _ORIGINAL_SHA256
        or json.dumps is not _ORIGINAL_JSON_DUMPS
        or _RESULT_DOMAIN is not _ORIGINAL_RESULT_DOMAIN
    ):
        raise MemoryCoherentHistoryRejected(
            "coherent Memory digest implementation or domain changed"
        )
    if (
        RetainedCoherentMemoryReview is not _RESULT
        or any(
            vars(_RESULT).get(name) is not old
            for names, originals in (
                (_RESULT_FIELDS, _ORIGINAL_RESULT_FIELDS),
                (_RESULT_DENIALS, _ORIGINAL_RESULT_DENIALS),
                (_RESULT_HOOKS, _ORIGINAL_RESULT_HOOKS),
            )
            for name, old in zip(names, originals, strict=True)
        )
    ):
        raise MemoryCoherentHistoryRejected(
            "coherent result constructor or authority descriptor changed"
        )



def review_retained_coherent_memory(
    store: SQLiteMemoryStore,
    prior_prefix: prefix.MemoryEventPrefixWitness,
    prior_alignment: alignment.MemoryEventAlignmentReview,
    *,
    prior_rows: row_delta.MemoryRowDeltaWitness | None = None,
) -> RetainedCoherentMemoryReview:
    """Recheck an old event prefix and current live rows in one local read TX.

    Preserve previous witnesses outside this SQLite file. The optional
    per-row witness binds unchanged old rows even when another memory has
    appended events; it is inspected in the SAME read transaction as the
    event-prefix and lifecycle checks. None authenticates custody or writer.
    A row with its own appended event is not authenticated by that event.
    """
    _require_original_result_carrier()
    if type(store) is not _STORE:
        raise MemoryCoherentHistoryRejected("exact Memory source required")
    try:
        old_prefix = prefix._witness_epoch(prior_prefix)
        old_alignment = retained_alignment._epoch(prior_alignment)
    except MemorySchemaError as exc:
        raise MemoryCoherentHistoryRejected("invalid retained witness") from exc
    if (
        old_prefix[0] != old_alignment[1]
        or old_prefix[1] != old_alignment[3]
    ):
        raise MemoryCoherentHistoryRejected("retained witnesses disagree on event epoch")
    try:
        old_rows = row_delta._validate(prior_rows) if prior_rows is not None else None
    except MemorySchemaError as exc:
        raise MemoryCoherentHistoryRejected("invalid retained row witness") from exc
    if old_rows is not None and old_rows[:3] != old_prefix:
        raise MemoryCoherentHistoryRejected("retained row witness event epoch differs")

    path = store.path

    def stable() -> None:
        _require_original_result_carrier()
        try:
            if (
                type(store) is not _STORE
                or store.path is not path
                or any(a is not b for a, b in zip(
                    prefix._witness_epoch(prior_prefix), old_prefix, strict=True,
                ))
                or any(a is not b for a, b in zip(
                    retained_alignment._epoch(prior_alignment),
                    old_alignment, strict=True,
                ))
                or (
                    old_rows is not None
                    and (
                        type(prior_rows) is not row_delta.MemoryRowDeltaWitness
                        or prior_rows.event_count is not old_rows[0]
                        or prior_rows.last_event_id is not old_rows[1]
                        or prior_rows.event_prefix_sha256 is not old_rows[2]
                        or prior_rows.rows is not old_rows[3]
                        or prior_rows.independently_authenticated is not False
                        or prior_rows.historical_writer_authenticated is not False
                        or prior_rows.disclosure_authorized is not False
                        or prior_rows.action_authorized is not False
                    )
                )
            ):
                raise MemoryCoherentHistoryRejected(
                    "retained source/witness changed during coherent read"
                )
        except MemoryCoherentHistoryRejected:
            raise
        except MemorySchemaError as exc:
            raise MemoryCoherentHistoryRejected("retained witness changed") from exc

    stable()
    aligned_hash = hashlib.sha256(alignment._DOMAIN)
    event_hash = hashlib.sha256(prefix._DOMAIN)
    prior_hash = hashlib.sha256(prefix._DOMAIN)
    count = 0
    last_id = 0
    old_tail = 0
    rows = 0
    scopes: set[tuple[str, str]] = set()
    current: dict[str, tuple[str, str, int, int, int]] = {}
    lifecycle: dict[str, tuple[str, str, int, bool, int, int]] = {}
    row_commitments: dict[str, tuple[str, int, str]] = {}
    touched_after_retained: set[str] = set()

    try:
        stable()
        with closing(store._connect_readonly()) as conn:
            stable()
            conn.execute("BEGIN")
            try:
                # Schema validation pins the WAL read snapshot before any
                # caller-controlled record decoding or hash callbacks.
                _validate_v1_schema(conn)
                stable()
                for row in conn.execute("SELECT * FROM memories ORDER BY memory_id"):
                    rows += 1
                    if rows > _MAX_ROWS:
                        raise MemoryCoherentHistoryRejected("coherent row scan budget exceeded")
                    try:
                        record = _record(row)
                    except MemorySchemaError as exc:
                        raise MemoryCoherentHistoryRejected(
                            "invalid stored Memory row"
                        ) from exc
                    stable()
                    memory_id = record.memory_id
                    owner = record.scope.owner_id
                    namespace = record.scope.namespace
                    if memory_id in current:
                        raise MemoryCoherentHistoryRejected("duplicate live Memory identity")
                    current[memory_id] = (
                        owner, namespace, record.revision,
                        record.created_at_ms, record.updated_at_ms,
                    )
                    if old_rows is not None:
                        row_commitments[memory_id] = row_delta._commitment(row)
                    scopes.add((owner, namespace))
                    metadata_hash = hashlib.sha256(
                        row["metadata_json"].encode("utf-8")
                    ).hexdigest()
                    alignment._charge(aligned_hash, (
                        "row", memory_id, owner, namespace, record.source_id,
                        record.revision, record.content_sha256, metadata_hash,
                        record.created_at_ms, record.updated_at_ms, record.expires_at_ms,
                    ))
                    stable()

                for event in conn.execute(
                    "SELECT event_id,memory_id,owner_id,namespace,operation,"
                    "revision,occurred_at_ms FROM memory_events ORDER BY event_id"
                ):
                    count += 1
                    if count > _MAX_EVENTS:
                        raise MemoryCoherentHistoryRejected(
                            "coherent event scan budget exceeded"
                        )
                    event_id, memory_id, owner, namespace, operation, revision, at = event
                    if (
                        type(event_id) is not int or not last_id < event_id <= SQLITE_INT_MAX
                        or type(memory_id) is not str
                        or prefix._ID.fullmatch(memory_id) is None
                        or type(operation) is not str or operation not in prefix._OPERATIONS
                        or type(revision) is not int or not 1 <= revision <= SQLITE_INT_MAX
                        or type(at) is not int or not 0 <= at <= SQLITE_INT_MAX
                    ):
                        raise MemoryCoherentHistoryRejected("invalid coherent Memory event")
                    # This v1 event journal is globally dense across all
                    # owners. A missing event in an unrelated scope must not
                    # become an apparently valid appended suffix.
                    if event_id != last_id + 1:
                        raise MemoryCoherentHistoryRejected(
                            "coherent Memory event ID gap"
                        )
                    try:
                        MemoryScope(owner, namespace)
                    except (TypeError, ValueError) as exc:
                        raise MemoryCoherentHistoryRejected(
                            "invalid coherent Memory event scope"
                        ) from exc
                    previous = lifecycle.get(memory_id)
                    if previous is not None and previous[:2] != (owner, namespace):
                        raise MemoryCoherentHistoryRejected("Memory event identity changed scope")
                    if operation == "create":
                        if revision != 1 or previous is not None and previous[3]:
                            raise MemoryCoherentHistoryRejected(
                                "invalid coherent creation lifecycle"
                            )
                        active = True
                        created_at = at
                        last_write_at = at
                    else:
                        if previous is None or not previous[3]:
                            raise MemoryCoherentHistoryRejected(
                                "coherent event without active Memory"
                            )
                        expected = previous[2] + (operation == "update")
                        if revision != expected:
                            raise MemoryCoherentHistoryRejected(
                                "coherent event revision changed"
                            )
                        active = operation == "update"
                        created_at = previous[4]
                        last_write_at = at if active else previous[5]
                    lifecycle[memory_id] = (
                        owner, namespace, revision, active, created_at, last_write_at,
                    )
                    scopes.add((owner, namespace))
                    entry = (
                        event_id, memory_id, owner, namespace, operation, revision, at,
                    )
                    prefix._charge(event_hash, entry)
                    if count <= old_prefix[0]:
                        prefix._charge(prior_hash, entry)
                        old_tail = event_id
                    elif old_rows is not None:
                        touched_after_retained.add(memory_id)
                    alignment._charge(aligned_hash, ("event",) + entry)
                    last_id = event_id
                    stable()

                for memory_id, state in lifecycle.items():
                    found = current.pop(memory_id, None)
                    if state[3]:
                        # Timestamp provenance belongs to this memory's own
                        # CREATE/last UPDATE, not to an unrelated owner's
                        # newly appended event. Clocks need not be monotonic.
                        if found != (
                            state[0], state[1], state[2], state[4], state[5],
                        ):
                            raise MemoryCoherentHistoryRejected(
                                "live Memory row/time differs from event lifecycle"
                            )
                    elif found is not None:
                        raise MemoryCoherentHistoryRejected(
                            "terminal event left a live Memory row"
                        )
                if current:
                    raise MemoryCoherentHistoryRejected(
                        "live Memory row lacks creation event"
                    )
                if old_rows is not None:
                    # Verify row deltas against the SAME WAL snapshot. Another
                    # memory's new event does not excuse an old row rewrite.
                    before_rows = {item[0]: item for item in old_rows[3]}
                    for identifier in before_rows.keys() | row_commitments.keys():
                        if (
                            before_rows.get(identifier) != row_commitments.get(identifier)
                            and identifier not in touched_after_retained
                        ):
                            raise MemoryCoherentHistoryRejected(
                                "Memory row changed without its own appended event"
                            )
                # Capture SQLite AUTOINCREMENT's local committed high-water
                # in the SAME WAL snapshot as rows and the entire event scan.
                # A deleted suffix can leave a dense surviving history, so a
                # retained prefix alone cannot detect it. This is still not
                # independently authenticated provenance.
                sequences = conn.execute(
                    "SELECT seq FROM sqlite_sequence WHERE name='memory_events'"
                ).fetchall()
                if (
                    (count == 0 and sequences)
                    or (count > 0 and (
                        len(sequences) != 1
                        or type(sequences[0][0]) is not int
                        or sequences[0][0] != last_id
                    ))
                ):
                    raise MemoryCoherentHistoryRejected(
                        "coherent Memory append high-water mismatch"
                    )
                stable()
                conn.rollback()
            except BaseException:
                conn.rollback()
                raise
    except sqlite3.Error as exc:
        raise MemoryCoherentHistoryRejected(
            "coherent Memory read-only snapshot unavailable"
        ) from exc

    stable()
    if count < old_prefix[0] or last_id < old_prefix[1]:
        raise MemoryCoherentHistoryRejected("retained Memory event tail rolled back")
    if (old_tail, prior_hash.hexdigest()) != (old_prefix[1], old_prefix[2]):
        raise MemoryCoherentHistoryRejected("retained Memory event prefix rewritten")
    if len(scopes) < old_alignment[2]:
        raise MemoryCoherentHistoryRejected("retained Memory scope history regressed")
    current_alignment_sha = aligned_hash.hexdigest()
    current_event_sha = event_hash.hexdigest()
    if count == old_prefix[0] and (
        last_id != old_alignment[3]
        or rows != old_alignment[0]
        or len(scopes) != old_alignment[2]
        or current_alignment_sha != old_alignment[4]
    ):
        raise MemoryCoherentHistoryRejected(
            "Memory changed without new recorded event"
        )
    status = (
        "ADVANCED_PREFIX_UNAUTHENTICATED"
        if count > old_prefix[0] else "UNCHANGED_LOCAL_HISTORY"
    )
    row_witness_root = (
        hashlib.sha256(
            row_delta._DOMAIN + json.dumps(
                old_rows, separators=(",", ":"), ensure_ascii=True,
            ).encode("ascii")
        ).hexdigest()
        if old_rows is not None else None
    )
    payload = json.dumps(
        (old_prefix, old_alignment, rows, count, len(scopes), last_id,
         current_alignment_sha, current_event_sha, status, row_witness_root),
        separators=(",", ":"), ensure_ascii=True,
    ).encode("ascii")
    stable()
    digest = hashlib.sha256(_RESULT_DOMAIN + payload).hexdigest()
    stable()
    report = _RESULT(
        old_prefix[0], count, rows, len(scopes), last_id, status,
        current_alignment_sha, current_event_sha, digest,
        old_rows is not None,
    )
    stable()
    if (
        type(report) is not _RESULT
        or type(report.previous_event_count) is not int
        or report.previous_event_count != old_prefix[0]
        or type(report.current_event_count) is not int
        or report.current_event_count != count
        or type(report.row_count) is not int or report.row_count != rows
        or type(report.scope_count) is not int or report.scope_count != len(scopes)
        or type(report.last_event_id) is not int or report.last_event_id != last_id
        or report.status is not status
        or report.current_alignment_sha256 is not current_alignment_sha
        or report.current_event_sha256 is not current_event_sha
        or report.review_sha256 is not digest
        or report.retained_row_delta_checked is not (old_rows is not None)
        or report.independently_authenticated is not False
        or report.historical_writer_authenticated is not False
        or report.consent_verified is not False
        or report.memory_disclosure_authorized is not False
        or report.action_authorized is not False
        or report.cross_store_atomicity_proven is not False
    ):
        raise MemoryCoherentHistoryRejected("coherent result acquired authority")
    stable()
    # Every flag above is an overridable property callback, including the
    # LAST cross_store_atomicity_proven getter. A false-valued getter must not
    # alter the report after the earlier digest/field check.
    if (
        type(report) is not _RESULT
        or type(report.previous_event_count) is not int
        or report.previous_event_count != old_prefix[0]
        or type(report.current_event_count) is not int
        or report.current_event_count != count
        or type(report.row_count) is not int or report.row_count != rows
        or type(report.scope_count) is not int
        or report.scope_count != len(scopes)
        or type(report.last_event_id) is not int
        or report.last_event_id != last_id
        or report.status is not status
        or report.current_alignment_sha256 is not current_alignment_sha
        or report.current_event_sha256 is not current_event_sha
        or report.review_sha256 is not digest
        or report.retained_row_delta_checked is not (old_rows is not None)
    ):
        raise MemoryCoherentHistoryRejected(
            "coherent report changed after final denial callback"
        )
    return report
