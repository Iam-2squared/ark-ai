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
from .contracts import MemorySchemaError, MemoryScope
from .sqlite_store import SQLITE_INT_MAX, SQLiteMemoryStore, _record, _validate_v1_schema

_MAX_ROWS = 10_000
_MAX_EVENTS = 40_000
_RESULT_DOMAIN = b"ARK-memory-retained-coherent-snapshot-v1\0"


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


def review_retained_coherent_memory(
    store: SQLiteMemoryStore,
    prior_prefix: prefix.MemoryEventPrefixWitness,
    prior_alignment: alignment.MemoryEventAlignmentReview,
) -> RetainedCoherentMemoryReview:
    """Recheck an old event prefix and current live rows in one local read TX.

    Preserve BOTH previous witnesses outside this SQLite file. Neither
    witness attests its own custody. When a valid event tail has advanced,
    the current row state is checked for lifecycle consistency, but arbitrary
    older row bytes cannot be reconstructed from the v1 event schema.
    """
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

    path = store.path

    def stable() -> None:
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
    current: dict[str, tuple[str, str, int]] = {}
    lifecycle: dict[str, tuple[str, str, int, bool]] = {}

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
                    current[memory_id] = (owner, namespace, record.revision)
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
                    lifecycle[memory_id] = (owner, namespace, revision, active)
                    scopes.add((owner, namespace))
                    entry = (
                        event_id, memory_id, owner, namespace, operation, revision, at,
                    )
                    prefix._charge(event_hash, entry)
                    if count <= old_prefix[0]:
                        prefix._charge(prior_hash, entry)
                        old_tail = event_id
                    alignment._charge(aligned_hash, ("event",) + entry)
                    last_id = event_id
                    stable()

                for memory_id, state in lifecycle.items():
                    found = current.pop(memory_id, None)
                    if state[3]:
                        if found != state[:3]:
                            raise MemoryCoherentHistoryRejected(
                                "live Memory row differs from event lifecycle"
                            )
                    elif found is not None:
                        raise MemoryCoherentHistoryRejected(
                            "terminal event left a live Memory row"
                        )
                if current:
                    raise MemoryCoherentHistoryRejected(
                        "live Memory row lacks creation event"
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
    payload = json.dumps(
        (old_prefix, old_alignment, rows, count, len(scopes), last_id,
         current_alignment_sha, current_event_sha, status),
        separators=(",", ":"), ensure_ascii=True,
    ).encode("ascii")
    stable()
    digest = hashlib.sha256(_RESULT_DOMAIN + payload).hexdigest()
    stable()
    report = _RESULT(
        old_prefix[0], count, rows, len(scopes), last_id, status,
        current_alignment_sha, current_event_sha, digest,
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
        or report.independently_authenticated is not False
        or report.historical_writer_authenticated is not False
        or report.consent_verified is not False
        or report.memory_disclosure_authorized is not False
        or report.action_authorized is not False
        or report.cross_store_atomicity_proven is not False
    ):
        raise MemoryCoherentHistoryRejected("coherent result acquired authority")
    stable()
    return report
