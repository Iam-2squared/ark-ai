"""Read-only triage after an ambiguous Memory generation-CAS COMMIT.

No retry, actor attribution, or exactly-once guarantee follows from a local
SQLite observation. The pre-write witness must be retained independently.
"""

from __future__ import annotations

import sqlite3
from contextlib import closing
from dataclasses import dataclass
from types import MappingProxyType

from .contracts import (
    MemoryConflictError,
    MemoryRecord,
    MemorySchemaError,
    MemoryScope,
    MemoryWrite,
)
from .generation_cas_outcome_review import _check_global_memory_event_highwater
from .generation_fenced_cas import (
    _EVENT_DOMAIN,
    _MAX_EVENTS,
    MemoryGenerationCASRejected,
    MemoryGenerationCASToken,
    _digest,
    _require_bounded_scope,
    _require_bounded_source_id,
    _require_original_generation_inputs,
    _require_original_token_denials,
    _row_hash,
    _snapshot,
    _token_fields,
)
from .sqlite_store import SQLITE_INT_MAX, SQLiteMemoryStore, deterministic_memory_id

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
_ORIGINAL_REPORT_INIT = vars(_REPORT)["__init__"]
_ORIGINAL_DENIALS = tuple(vars(_REPORT)[name] for name in _DENIALS)

_REPORT_FIELDS = (
    "memory_id", "retained_event_id", "observed_event_id",
    "retained_prefix_sha256", "observed_prefix_sha256", "disposition",
    "report_sha256",
)
_REPORT_HOOKS = ("__new__", "__getattribute__", "__getattr__")
_ORIGINAL_REPORT_FIELDS = tuple(vars(_REPORT)[name] for name in _REPORT_FIELDS)
_ORIGINAL_REPORT_HOOKS = tuple(vars(_REPORT).get(name) for name in _REPORT_HOOKS)
# Domain separation and bounded history are part of this manual-only
# diagnostic protocol. Never accept caller-rebound globals as reviewed input.
_ORIGINAL_DOMAIN = _DOMAIN
_ORIGINAL_EVENT_DOMAIN = _EVENT_DOMAIN
_ORIGINAL_MAX_EVENTS = _MAX_EVENTS
# The imported helpers below are consulted before looking at private retained
# tokens, proposed Memory content or the local SQLite row. Keep their original
# callable/module identities. The separately tested _snapshot/_row_hash/_digest
# injection seams are intentionally NOT made authoritative by this guard.
_ORIGINAL_SQLITE3 = sqlite3
_ORIGINAL_IDENTITY = deterministic_memory_id
_ORIGINAL_TOKEN_FIELDS = _token_fields
_ORIGINAL_INPUT_VALIDATOR = _require_original_generation_inputs
_ORIGINAL_TOKEN_VALIDATOR = _require_original_token_denials
_ORIGINAL_GLOBAL_HIGHWATER = _check_global_memory_event_highwater


def _require_original_report_carrier() -> None:
    """Reject executable report replacements before observing private Memory."""
    if (
        MemoryCommitTriage is not _REPORT
        or _DOMAIN is not _ORIGINAL_DOMAIN
        or _EVENT_DOMAIN is not _ORIGINAL_EVENT_DOMAIN
        or type(_MAX_EVENTS) is not int or _MAX_EVENTS != _ORIGINAL_MAX_EVENTS
        or sqlite3 is not _ORIGINAL_SQLITE3
        or deterministic_memory_id is not _ORIGINAL_IDENTITY
        or _token_fields is not _ORIGINAL_TOKEN_FIELDS
        or _require_original_generation_inputs is not _ORIGINAL_INPUT_VALIDATOR
        or _require_original_token_denials is not _ORIGINAL_TOKEN_VALIDATOR
        or _check_global_memory_event_highwater is not _ORIGINAL_GLOBAL_HIGHWATER
        or vars(_REPORT).get("__init__") is not _ORIGINAL_REPORT_INIT
        or any(
            vars(_REPORT).get(name) is not original
            for name, original in zip(
                _REPORT_FIELDS, _ORIGINAL_REPORT_FIELDS, strict=True,
            )
        )
        or any(
            vars(_REPORT).get(name) is not original
            for name, original in zip(
                _REPORT_HOOKS, _ORIGINAL_REPORT_HOOKS, strict=True,
            )
        )
        or any(
            vars(_REPORT).get(name) is not original
            for name, original in zip(_DENIALS, _ORIGINAL_DENIALS, strict=True)
        )
    ):
        raise MemoryCommitTriageRejected("Memory triage input or denial changed")



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
    _require_original_report_carrier()
    # Reject executable substitutions of frozen Memory v1 carrier slots before
    # accessing even proposed.scope; the triage path never invokes getters
    # installed by a caller to determine its own input identity.
    try:
        _require_original_generation_inputs()
    except MemoryGenerationCASRejected as exc:
        raise MemoryCommitTriageRejected(
            "Memory triage input carrier changed"
        ) from exc
    if (
        type(store) is not SQLiteMemoryStore
        or type(proposed) is not MemoryWrite
        or type(proposed.scope) is not MemoryScope
        or type(retained_before) is not MemoryGenerationCASToken
    ):
        raise MemoryCommitTriageRejected("exact Memory triage inputs required")
    _require_original_report_carrier()
    try:
        # The caller-retained witness is not consent or a tool capability.
        # Reject a False-looking substituted getter before it can execute.
        _require_original_token_denials()
        before = _token_fields(retained_before)
        # Reflective mutation of a frozen MemoryWrite must not let invalid
        # private content, scopes, expiry or mapping callbacks reach SQLite.
        # The opt-in CAS diagnostic uses the same UTF-8 byte limits as CAS;
        # frozen Memory v1 contracts and public CRUD semantics are unchanged.
        _require_bounded_scope(proposed.scope)
        _require_bounded_source_id(proposed.source_id)
        content_input = proposed.content
        if (
            type(content_input) is not str or not content_input.strip()
            or len(content_input) > 1_000_000
        ):
            raise MemoryCommitTriageRejected("invalid bounded Memory triage content")
        content_input.encode("utf-8", errors="strict")
        expiry_input = proposed.expires_at_ms
        if expiry_input is not None and (
            type(expiry_input) is not int
            or not 0 <= expiry_input <= SQLITE_INT_MAX
        ):
            raise MemoryCommitTriageRejected("invalid Memory triage expiry")
        metadata_input = proposed.metadata
        if (
            type(metadata_input) not in (dict, MappingProxyType)
            or len(metadata_input) > 64
        ):
            raise MemoryCommitTriageRejected("invalid Memory triage metadata mapping")
        for key, value in metadata_input.items():
            if (
                type(key) is not str or not key.strip() or len(key) > 4096
                or type(value) is not str or len(value) > 4096
            ):
                raise MemoryCommitTriageRejected("invalid Memory triage metadata")
            if (
                len(key.encode("utf-8", errors="strict")) > 4096
                or len(value.encode("utf-8", errors="strict")) > 4096
            ):
                raise MemoryCommitTriageRejected("oversized Memory triage metadata")
        memory_id = deterministic_memory_id(proposed.scope, proposed.source_id)
        if memory_id != before[0]:
            raise MemoryCommitTriageRejected("retained token targets another row")
        path, scope = store.path, proposed.scope
        owner, namespace = scope.owner_id, scope.namespace
        source, content = proposed.source_id, proposed.content
        expiry, carrier = proposed.expires_at_ms, proposed.metadata
        metadata = dict(carrier)
    except (MemoryGenerationCASRejected, TypeError, ValueError, UnicodeError) as exc:
        raise MemoryCommitTriageRejected("invalid retained Memory triage inputs") from exc

    def stable() -> None:
        _require_original_report_carrier()
        try:
            _require_original_generation_inputs()
            _require_original_token_denials()
        except MemoryGenerationCASRejected as exc:
            raise MemoryCommitTriageRejected(
                "Memory triage token authority changed"
            ) from exc
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
            # A frozen, caller-retained token can still be reflectively
            # replaced with equal-valued digest strings during _snapshot or
            # a SQLite callback. Such a new carrier is NOT the original
            # pre-COMMIT witness and must never be used for manual triage.
            or any(
                now is not original
                for now, original in zip(
                    _token_fields(retained_before), before, strict=True,
                )
            )
            or MemoryCommitTriage is not _REPORT
            or vars(_REPORT).get("__init__") is not _ORIGINAL_REPORT_INIT
            or any(
                vars(_REPORT).get(name) is not original
                for name, original in zip(_DENIALS, _ORIGINAL_DENIALS, strict=True)
            )
        ):
            raise MemoryCommitTriageRejected("Memory triage input or denial changed")
        # Bracket every getter with the original class descriptor witness.
        # This cannot authenticate who created the token.
        for name in ("external_action_authorized", "consent_authenticated"):
            _require_original_token_denials()
            if getattr(retained_before, name) is not False:
                raise MemoryCommitTriageRejected(
                    "retained Memory CAS token claimed authority"
                )
            _require_original_token_denials()

    try:
        stable()
        with closing(store._connect_readonly()) as conn:
            conn.execute("BEGIN")
            stable()
            record, observed = _snapshot(conn, memory_id, scope, source)
            # A per-target CAS prefix can still look valid after another
            # scope's event was removed. Verify the global append high-water
            # inside the same BEGIN snapshot before classifying any outcome.
            _check_global_memory_event_highwater(conn)
            stable()
            after = _token_fields(observed)
            # The SQLite generation snapshot pins the row SHA at observation
            # time. The local record object can still be reflectively changed
            # by later synthetic callbacks; it must not become a forged match.
            if type(record) is not MemoryRecord:
                raise MemoryCommitTriageRejected("Memory triage row type changed")
            # The hash calculator is a synthetic reentrant callback. Save
            # exact row carriers before invoking it, and inspect them again
            # after it returns: a digest computed *before* a mutation cannot
            # prove that the returned object still represents the snapshot.
            row_epoch = (
                record.memory_id, record.scope, record.source_id,
                record.content, record.created_at_ms, record.updated_at_ms,
                record.expires_at_ms, record.revision, record.content_sha256,
                record.metadata,
            )
            metadata_epoch = dict(record.metadata)

            def row_carriers_intact() -> bool:
                return (
                    type(record) is MemoryRecord
                    and all(now is prior for now, prior in zip(
                        (
                            record.memory_id, record.scope, record.source_id,
                            record.content, record.created_at_ms,
                            record.updated_at_ms, record.expires_at_ms,
                            record.revision, record.content_sha256,
                            record.metadata,
                        ), row_epoch, strict=True,
                    ))
                    and dict(record.metadata) == metadata_epoch
                )

            def stable_row() -> None:
                if not row_carriers_intact():
                    raise MemoryCommitTriageRejected(
                        "Memory triage row image changed after snapshot"
                    )
                calculated = _row_hash(record)
                if calculated != after[5] or not row_carriers_intact():
                    raise MemoryCommitTriageRejected(
                        "Memory triage row image changed after snapshot"
                    )

            stable_row()
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
            stable_row()
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
            stable_row()
    except (
        sqlite3.Error, MemoryConflictError, MemoryGenerationCASRejected,
        MemorySchemaError, ValueError, TypeError, AttributeError,
    ) as exc:
        raise MemoryCommitTriageRejected(
            "Memory triage unavailable; manual review required"
        ) from exc

    # Connection teardown may also be a callback boundary. Never report a
    # matching row image after losing the previously observed row digest.
    stable_row()
    payload = (
        memory_id, before[2], after[2], before[4], after[4], disposition,
    )
    # A close hook or report-digest callback can install executable code
    # into the result constructor after the last in-transaction check.
    # Refuse before invoking it, even for a False-only report.
    report_digest = _digest(_DOMAIN, payload)
    stable()
    report = _REPORT(*payload, report_digest)
    stable()
    fields = (*payload, report.report_sha256)

    def stable_report() -> None:
        stable()
        stable_row()
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
