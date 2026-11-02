"""Read-only triage after an ambiguous Memory generation-CAS COMMIT.

No retry, actor attribution, or exactly-once guarantee follows from a local
SQLite observation. The pre-write witness must be retained independently.
"""

from __future__ import annotations

import sqlite3
from contextlib import closing
from dataclasses import dataclass

from .contracts import MemoryConflictError, MemorySchemaError, MemoryScope, MemoryWrite
from .generation_fenced_cas import (
    _EVENT_DOMAIN,
    _MAX_EVENTS,
    MemoryGenerationCASRejected,
    MemoryGenerationCASToken,
    _digest,
    _snapshot,
    _token_fields,
)
from .sqlite_store import SQLiteMemoryStore, deterministic_memory_id

_DOMAIN = b"ARK-memory-postcommit-manual-triage-v1\0"
_DENIALS = (
    "automatic_retry_authorized", "write_authorized",
    "caller_attribution_proven", "trusted_clock_proven",
)


class MemoryCommitTriageRejected(MemorySchemaError):
    """Local history cannot be safely classified; manual review required."""


@dataclass(frozen=True, slots=True)
class MemoryCommitTriage:
    memory_id: str
    retained_event_id: int
    observed_event_id: int
    retained_prefix_sha256: str
    observed_prefix_sha256: str
    disposition: str
    report_sha256: str

    @property
    def automatic_retry_authorized(self) -> bool:
        return False

    @property
    def write_authorized(self) -> bool:
        return False

    @property
    def caller_attribution_proven(self) -> bool:
        return False

    @property
    def trusted_clock_proven(self) -> bool:
        return False


_REPORT = MemoryCommitTriage
_ORIGINAL_DENIALS = tuple(getattr(_REPORT, name) for name in _DENIALS)


def review_uncertain_memory_commit(
    store: SQLiteMemoryStore,
    proposed: MemoryWrite,
    *,
    retained_before: MemoryGenerationCASToken,
) -> MemoryCommitTriage:
    """Read one bounded snapshot; produce only a manual diagnostic.

    LOCAL_UNCHANGED means prior row/history remains locally visible.
    ONE_MATCHING_UPDATE_VISIBLE means one new update matches the proposed
    row image but its author and cause remain UNPROVEN.
    INDETERMINATE means other changes were observed.
    Neither disposition is permission to retry, dispatch, erase or promote.
    """
    if (
        type(store) is not SQLiteMemoryStore
        or type(proposed) is not MemoryWrite
        or type(proposed.scope) is not MemoryScope
        or type(retained_before) is not MemoryGenerationCASToken
    ):
        raise MemoryCommitTriageRejected("exact Memory triage inputs required")
    try:
        before = _token_fields(retained_before)
        memory_id = deterministic_memory_id(proposed.scope, proposed.source_id)
        if memory_id != before[0]:
            raise MemoryCommitTriageRejected("retained token targets another row")
        path, scope = store.path, proposed.scope
        owner, namespace = scope.owner_id, scope.namespace
        source, content = proposed.source_id, proposed.content
        expiry, carrier = proposed.expires_at_ms, proposed.metadata
        metadata = dict(carrier)
    except (MemoryGenerationCASRejected, TypeError, ValueError) as exc:
        raise MemoryCommitTriageRejected("invalid retained Memory triage inputs") from exc

    def stable() -> None:
        if (
            type(store) is not SQLiteMemoryStore
            or store.path is not path
            or proposed.scope is not scope
            or scope.owner_id is not owner
            or scope.namespace is not namespace
            or proposed.source_id is not source
            or proposed.content is not content
            or proposed.expires_at_ms is not expiry
            or proposed.metadata is not carrier
            or dict(proposed.metadata) != metadata
            or _token_fields(retained_before) != before
            or any(
                getattr(_REPORT, name) is not original
                for name, original in zip(_DENIALS, _ORIGINAL_DENIALS, strict=True)
            )
        ):
            raise MemoryCommitTriageRejected("Memory triage input or denial changed")

    try:
        stable()
        with closing(store._connect_readonly()) as conn:
            conn.execute("BEGIN")
            stable()
            record, observed = _snapshot(conn, memory_id, scope, source)
            after = _token_fields(observed)
            rows = conn.execute(
                "SELECT event_id,owner_id,namespace,operation,revision,occurred_at_ms "
                "FROM memory_events WHERE memory_id=? ORDER BY event_id LIMIT ?",
                (memory_id, _MAX_EVENTS + 1),
            ).fetchall()
            events = tuple(tuple(row) for row in rows)
            stable()
            if not events or len(events) > _MAX_EVENTS:
                raise MemoryCommitTriageRejected("Memory events unavailable")
            if _digest(_EVENT_DOMAIN, events) != after[4]:
                raise MemoryCommitTriageRejected("Memory event scan changed")
            prefix = tuple(row for row in events if row[0] <= before[2])
            if (
                not prefix or prefix[-1][0] != before[2]
                or _digest(_EVENT_DOMAIN, prefix) != before[4]
            ):
                raise MemoryCommitTriageRejected(
                    "retained Memory history is not a current prefix"
                )
            if after == before:
                disposition = "LOCAL_UNCHANGED"
            elif (
                after[1] == before[1]
                and after[3] == before[3] + 1
                and len(events) == len(prefix) + 1
                and events[-1][3] == "update"
                and record.content == content
                and dict(record.metadata) == metadata
                and record.expires_at_ms == expiry
            ):
                disposition = "ONE_MATCHING_UPDATE_VISIBLE"
            else:
                disposition = "INDETERMINATE"
            stable()
    except (
        sqlite3.Error, MemoryConflictError, MemoryGenerationCASRejected,
        MemorySchemaError, ValueError, TypeError, AttributeError,
    ) as exc:
        raise MemoryCommitTriageRejected(
            "Memory triage unavailable; manual review required"
        ) from exc

    payload = (
        memory_id, before[2], after[2], before[4], after[4], disposition,
    )
    report = _REPORT(*payload, _digest(_DOMAIN, payload))
    fields = (*payload, report.report_sha256)

    def stable_report() -> None:
        stable()
        if (
            type(report) is not _REPORT
            or any(now is not old for now, old in zip(
                (
                    report.memory_id, report.retained_event_id,
                    report.observed_event_id, report.retained_prefix_sha256,
                    report.observed_prefix_sha256, report.disposition,
                    report.report_sha256,
                ),
                fields, strict=True,
            ))
        ):
            raise MemoryCommitTriageRejected("Memory triage report changed")

    stable_report()
    for name in _DENIALS:
        if getattr(report, name) is not False:
            raise MemoryCommitTriageRejected("Memory triage claimed authority")
        stable_report()
    return report
