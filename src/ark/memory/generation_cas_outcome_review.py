"""Read-only post-COMMIT ambiguity review for opt-in Memory generation CAS.

A matching row is NOT proof that this invocation committed it: another writer
can persist identical bytes. No observed state grants retry, consent, trusted
time, deletion, live actions, or permission to relax retention. Unavailable,
missing, regressed or replaced generation history is a manual-only blocker.
The frozen Memory v1 schema and put/delete API are unchanged.
"""

from __future__ import annotations

import hashlib
import json
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
from .generation_fenced_cas import (
    _EVENT_DOMAIN,
    _MAX_EVENTS,
    MemoryGenerationCASRejected,
    MemoryGenerationCASToken,
    _digest,
    _require_bounded_scope,
    _require_bounded_source_id,
    _require_original_generation_inputs,
    _row_hash,
    _snapshot,
    _token_fields,
)
from .sqlite_store import SQLITE_INT_MAX, SQLiteMemoryStore, deterministic_memory_id

_DOMAIN = b"ARK-memory-generation-cas-ambiguous-observation-v1\0"
_DENIED = (
    "commit_attributed_to_caller",
    "automatic_retry_authorized",
    "consent_authenticated",
    "trusted_clock_verified",
    "external_action_authorized",
)


class MemoryCASOutcomeRejected(MemorySchemaError):
    """No coherent manual-only post-COMMIT observation is available."""


@dataclass(frozen=True, slots=True)
class MemoryCASOutcomeReview:
    observation: str
    retained_prefix_sha256: str
    observed_prefix_sha256: str
    observed_row_sha256: str
    expected_content_sha256: str
    review_sha256: str

    @property
    def commit_attributed_to_caller(self) -> bool:
        return False

    @property
    def automatic_retry_authorized(self) -> bool:
        return False

    @property
    def consent_authenticated(self) -> bool:
        return False

    @property
    def trusted_clock_verified(self) -> bool:
        return False

    @property
    def external_action_authorized(self) -> bool:
        return False


_REPORT_TYPE = MemoryCASOutcomeReview
_ORIGINAL_REPORT_INIT = vars(_REPORT_TYPE)["__init__"]
_ORIGINAL_DENIALS = tuple(vars(_REPORT_TYPE)[name] for name in _DENIED)
_REPORT_FIELDS = (
    "observation", "retained_prefix_sha256", "observed_prefix_sha256",
    "observed_row_sha256", "expected_content_sha256", "review_sha256",
)
_REPORT_HOOKS = ("__new__", "__getattribute__", "__getattr__")
_ORIGINAL_REPORT_FIELDS = tuple(vars(_REPORT_TYPE)[name] for name in _REPORT_FIELDS)
_ORIGINAL_REPORT_HOOKS = tuple(vars(_REPORT_TYPE).get(name) for name in _REPORT_HOOKS)
# Digest callbacks touch private content and supply locally checked receipts.
# Before hashing or opening SQLite, reject substituted implementations and
# domain separation, including equal-valued replacement domain objects.
_ORIGINAL_HASHLIB = hashlib
_ORIGINAL_JSON = json
_ORIGINAL_SHA256 = hashlib.sha256
_ORIGINAL_DUMPS = json.dumps
_ORIGINAL_DOMAIN = _DOMAIN


def _require_original_denials() -> None:
    if (
        hashlib is not _ORIGINAL_HASHLIB
        or json is not _ORIGINAL_JSON
        or hashlib.sha256 is not _ORIGINAL_SHA256
        or json.dumps is not _ORIGINAL_DUMPS
        or _DOMAIN is not _ORIGINAL_DOMAIN
    ):
        raise MemoryCASOutcomeRejected("CAS outcome digest implementation changed")
    # The cross-scope SQLite high-water check is mandatory, not an optional
    # diagnostic callback. A substituted no-op could otherwise turn an event
    # gap into an apparently coherent, non-authorizing CAS observation.
    if _check_global_memory_event_highwater is not _ORIGINAL_GLOBAL_HIGHWATER_CHECK:
        raise MemoryCASOutcomeRejected("CAS global history validator changed")
    # The properties alone do not authenticate their owning class: a caller
    # could attach the original False-valued descriptors to a counterfeit
    # report class with an executable constructor.
    if (
        MemoryCASOutcomeReview is not _REPORT_TYPE
        or vars(_REPORT_TYPE).get("__init__") is not _ORIGINAL_REPORT_INIT
        # A frozen, slotted dataclass can still have its field descriptors or
        # attribute lookup hooks replaced. Inspect class dictionaries BEFORE
        # touching a result instance or reading private SQLite content.
        or any(
            vars(_REPORT_TYPE).get(name) is not original
            for name, original in zip(
                _REPORT_FIELDS, _ORIGINAL_REPORT_FIELDS, strict=True,
            )
        )
        or any(
            vars(_REPORT_TYPE).get(name) is not original
            for name, original in zip(
                _REPORT_HOOKS, _ORIGINAL_REPORT_HOOKS, strict=True,
            )
        )
        or any(
            vars(_REPORT_TYPE).get(name) is not original
            for name, original in zip(_DENIED, _ORIGINAL_DENIALS, strict=True)
        )
    ):
        raise MemoryCASOutcomeRejected("CAS outcome authority definition changed")


def _check_global_memory_event_highwater(conn: sqlite3.Connection) -> None:
    """Refuse missing unrelated Memory events in the SAME observation snapshot.

    A target row's retained prefix can appear coherent after unrelated events
    were removed. This local AUTOINCREMENT check covers the whole append log;
    it is NOT independent historical provenance or a durable external anchor.
    """
    count, first, last = conn.execute(
        "SELECT COUNT(*),MIN(event_id),MAX(event_id) FROM memory_events"
    ).fetchone()
    # sqlite_sequence.name has no UNIQUE constraint. Require exactly one
    # committed marker, rather than accepting an arbitrary fetchone() row.
    markers = conn.execute(
        "SELECT seq FROM sqlite_sequence WHERE name='memory_events'"
    ).fetchall()
    if (
        type(count) is not int or count < 0
        or (count == 0 and (first is not None or last is not None or markers))
        or (
            count > 0
            and (
                type(first) is not int or first != 1
                or type(last) is not int or last != count
                or last > SQLITE_INT_MAX
                or len(markers) != 1
                or type(markers[0][0]) is not int
                or markers[0][0] != last
            )
        )
    ):
        raise MemoryCASOutcomeRejected(
            "CAS global Memory event high-water mismatch; manual review required"
        )


_ORIGINAL_GLOBAL_HIGHWATER_CHECK = _check_global_memory_event_highwater


def review_memory_generation_cas_outcome(
    store: SQLiteMemoryStore,
    proposed: MemoryWrite,
    *,
    retained: MemoryGenerationCASToken,
) -> MemoryCASOutcomeReview:
    """Observe an uncertain update in read-only snapshots, without replay.

    UNCHANGED_OBSERVED: the retained row and history are still present.
    ONE_MATCHING_UPDATE_OBSERVED: one newer revision has matching payload;
        this NEVER attributes the commit to this caller.
    DIVERGED_OBSERVED: a valid same-generation row differs from the proposal.
    Missing/deleted/recreated/invalid rows are rejected for manual triage.
    Every category is advisory, non-authorizing and time-limited.
    """
    # Validate original Memory v1 carrier descriptors before accessing a
    # proposed field. Frozen instances do not freeze their class slots.
    try:
        _require_original_generation_inputs()
    except MemoryGenerationCASRejected as exc:
        raise MemoryCASOutcomeRejected("CAS observation input carrier changed") from exc
    if (
        type(store) is not SQLiteMemoryStore
        or type(proposed) is not MemoryWrite
        or type(proposed.scope) is not MemoryScope
    ):
        raise MemoryCASOutcomeRejected("exact Memory CAS observation inputs required")
    _require_original_denials()
    prior = _token_fields(retained)
    scope = proposed.scope
    owner, namespace = scope.owner_id, scope.namespace
    source, content = proposed.source_id, proposed.content
    # MemoryWrite is frozen but reflectively mutable. Do not hash caller-private
    # data, inspect metadata, or open SQLite with an invalid post-init source
    # identity/content epoch. This opt-in review follows generation-CAS's
    # stricter 512-byte source rule, without changing Memory v1 behavior.
    try:
        _require_bounded_scope(scope)
    except MemoryGenerationCASRejected as exc:
        raise MemoryCASOutcomeRejected(
            "CAS observation requires bounded valid UTF-8 scope"
        ) from exc
    try:
        _require_bounded_source_id(source)
    except MemoryGenerationCASRejected as exc:
        raise MemoryCASOutcomeRejected(
            "CAS observation requires bounded valid UTF-8 source"
        ) from exc
    if (
        type(content) is not str or not content.strip()
        or len(content) > 1_000_000
    ):
        raise MemoryCASOutcomeRejected("CAS observation requires exact bounded content")
    try:
        content_bytes = content.encode("utf-8", errors="strict")
    except UnicodeError as exc:
        raise MemoryCASOutcomeRejected(
            "CAS observation requires valid UTF-8 content"
        ) from exc
    metadata = proposed.metadata
    expiry = proposed.expires_at_ms
    if expiry is not None and (
        type(expiry) is not int or not 0 <= expiry <= SQLITE_INT_MAX
    ):
        raise MemoryCASOutcomeRejected("CAS observation requires SQLite-range expiry")
    if type(metadata) not in (dict, MappingProxyType) or len(metadata) > 64:
        raise MemoryCASOutcomeRejected("CAS observation requires bounded plain metadata")
    # MemoryWrite's frozen v1 initializer validates metadata, but an opt-in
    # review can be given a reflectively changed proposal after construction.
    # Do not inspect a private SQLite row for a payload that cannot be
    # represented as the exact UTF-8 JSON accepted by generation CAS.
    try:
        expected_metadata = dict(metadata)
        if (
            len(expected_metadata) > 64
            or any(
                type(key) is not str or not key.strip() or len(key) > 4096
                or type(value) is not str or len(value) > 4096
                for key, value in expected_metadata.items()
            )
        ):
            raise MemoryCASOutcomeRejected(
                "CAS observation requires bounded string metadata"
            )
        json.dumps(
            expected_metadata, ensure_ascii=False, sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8", errors="strict")
    except (TypeError, ValueError, UnicodeError, AttributeError) as exc:
        raise MemoryCASOutcomeRejected(
            "CAS observation requires valid UTF-8 string metadata"
        ) from exc
    path = store.path
    memory_id = deterministic_memory_id(scope, source)
    if prior[0] != memory_id:
        raise MemoryCASOutcomeRejected("retained generation belongs to another row")
    expected_content_sha = hashlib.sha256(content_bytes).hexdigest()

    def stable() -> None:
        _require_original_denials()
        try:
            _require_original_generation_inputs()
        except MemoryGenerationCASRejected as exc:
            raise MemoryCASOutcomeRejected("CAS observation input carrier changed") from exc
        if (
            type(store) is not SQLiteMemoryStore
            or store.path is not path
            or type(proposed) is not MemoryWrite
            or proposed.scope is not scope
            or scope.owner_id is not owner
            or scope.namespace is not namespace
            or proposed.source_id is not source
            or proposed.content is not content
            or proposed.metadata is not metadata
            or proposed.expires_at_ms is not expiry
            or dict(proposed.metadata) != expected_metadata
            # Equal-value carrier replacement is still a different custody
            # epoch. Callback-driven evidence reattachment must not silently
            # become the original retained CAS witness.
            or any(
                current is not original
                for current, original in zip(
                    _token_fields(retained), prior, strict=True,
                )
            )
        ):
            raise MemoryCASOutcomeRejected("CAS observation inputs changed")

    def inspect():
        stable()
        try:
            with closing(store._connect_readonly()) as conn:
                conn.execute("BEGIN")
                stable()
                record, observed = _snapshot(conn, memory_id, scope, source)
                stable()
                # A syntactically valid retained prefix is not evidence. Bind
                # it to the actual persisted history at the old event tip.
                rows = conn.execute(
                    "SELECT event_id,owner_id,namespace,operation,revision,occurred_at_ms "
                    "FROM memory_events WHERE memory_id=? AND event_id<=? "
                    "ORDER BY event_id LIMIT ?",
                    (memory_id, retained.last_event_id, _MAX_EVENTS + 1),
                ).fetchall()
                prefix = [tuple(row) for row in rows]
                if (
                    not prefix or len(prefix) > _MAX_EVENTS
                    or prefix[-1][0] != retained.last_event_id
                    or _digest(_EVENT_DOMAIN, prefix) != retained.event_prefix_sha256
                ):
                    raise MemoryCASOutcomeRejected(
                        "retained CAS event prefix disagrees with SQLite"
                    )
                stable()
                # A valid per-row prefix is insufficient when another scope's
                # event is missing or sqlite_sequence has been retargeted.
                # Read this evidence inside the same SQLite transaction.
                _check_global_memory_event_highwater(conn)
                stable()
                _, again = _snapshot(conn, memory_id, scope, source)
                # Dataclass __eq__ is replaceable in synthetic callbacks;
                # compare the exact row/event token bytes, never a patched
                # equality method when deciding whether a snapshot drifted.
                if _token_fields(observed) != _token_fields(again):
                    raise MemoryCASOutcomeRejected("CAS observation snapshot changed")
                stable()
        except (sqlite3.Error, MemoryConflictError, MemorySchemaError) as exc:
            raise MemoryCASOutcomeRejected(
                "CAS generation unavailable; manual inspection required"
            ) from exc
        stable()
        if observed.create_event_id != retained.create_event_id:
            raise MemoryCASOutcomeRejected("CAS generation replaced; manual review")
        if (
            observed.revision == retained.revision
            and observed.last_event_id == retained.last_event_id
            and observed.row_sha256 != retained.row_sha256
        ):
            raise MemoryCASOutcomeRejected("retained row contradicts same-version row")
        if (
            observed.last_event_id < retained.last_event_id
            or observed.revision < retained.revision
        ):
            raise MemoryCASOutcomeRejected("CAS history regressed; manual review")
        return record, observed

    record, observed = inspect()
    observed_epoch = _token_fields(observed)
    record_epoch = (
        record.memory_id, record.scope, record.source_id, record.content,
        record.metadata, dict(record.metadata), record.created_at_ms,
        record.updated_at_ms, record.expires_at_ms, record.revision,
        record.content_sha256,
    )

    # Capture row and nested scope identity, not merely its current values.
    # A synthetic second _snapshot callback can mutate the FIRST returned
    # record after its token hash is calculated, even when token snapshots
    # still agree. Never classify a forged row as an update.
    record_scope = record.scope
    record_scope_epoch = (record_scope.owner_id, record_scope.namespace)

    def intact_record() -> bool:
        return (
            type(record) is MemoryRecord
            and type(record.scope) is MemoryScope
            and record.scope is record_scope
            and record_scope.owner_id is record_scope_epoch[0]
            and record_scope.namespace is record_scope_epoch[1]
            and all(now is old for now, old in zip(
                (
                    record.memory_id, record.scope, record.source_id,
                    record.content, record.metadata, record.created_at_ms,
                    record.updated_at_ms, record.expires_at_ms, record.revision,
                    record.content_sha256,
                ),
                (
                    record_epoch[0], record_epoch[1], record_epoch[2],
                    record_epoch[3], record_epoch[4], record_epoch[6],
                    record_epoch[7], record_epoch[8], record_epoch[9],
                    record_epoch[10],
                ), strict=True,
            ))
            and dict(record.metadata) == record_epoch[5]
        )

    def stable_observation() -> None:
        if (
            type(observed) is not MemoryGenerationCASToken
            or any(now is not old for now, old in zip(
                _token_fields(observed), observed_epoch, strict=True,
            ))
            or not intact_record()
        ):
            raise MemoryCASOutcomeRejected("CAS observed row or event token changed")
        stable()
        # The observed row fingerprint was computed inside _snapshot. Rehash
        # the returned object and bracket this callback with identity checks:
        # a second synthetic snapshot or reentrant hash can otherwise rewrite
        # content/metadata after that fingerprint was recorded.
        if _row_hash(record) != observed.row_sha256 or not intact_record():
            raise MemoryCASOutcomeRejected("CAS observed row image no longer matches token")
        stable()

    stable_observation()
    if observed_epoch == prior:
        label = "UNCHANGED_OBSERVED"
    elif (
        observed.revision == retained.revision + 1
        and observed.last_event_id > retained.last_event_id
        and record.content == content
        and dict(record.metadata) == expected_metadata
        and record.expires_at_ms == expiry
        and record.content_sha256 == expected_content_sha
    ):
        label = "ONE_MATCHING_UPDATE_OBSERVED"
    else:
        label = "DIVERGED_OBSERVED"
    fields = (
        label, retained.event_prefix_sha256, observed.event_prefix_sha256,
        observed.row_sha256, expected_content_sha,
    )
    digest = hashlib.sha256(
        _DOMAIN + json.dumps(
            fields, separators=(",", ":"), ensure_ascii=True, allow_nan=False,
        ).encode("ascii")
    ).hexdigest()
    # Verify constructor identity immediately before invocation; a forged
    # dataclass __init__ is executable even if all denial flags remain False.
    _require_original_denials()
    result = _REPORT_TYPE(*fields, digest)
    pinned = tuple(getattr(result, name) for name in (
        "observation", "retained_prefix_sha256", "observed_prefix_sha256",
        "observed_row_sha256", "expected_content_sha256", "review_sha256",
    ))
    descriptors = _ORIGINAL_DENIALS

    def stable_result() -> None:
        _require_original_denials()
        current = tuple(getattr(result, name) for name in (
            "observation", "retained_prefix_sha256", "observed_prefix_sha256",
            "observed_row_sha256", "expected_content_sha256", "review_sha256",
        ))
        if (
            type(result) is not MemoryCASOutcomeReview
            or any(now is not old for now, old in zip(
                current, pinned, strict=True,
            ))
            or any(vars(MemoryCASOutcomeReview).get(name) is not desc
                   for name, desc in zip(_DENIED, descriptors, strict=True))
        ):
            raise MemoryCASOutcomeRejected("CAS observation report changed")
        stable_observation()

    stable_result()
    for name in _DENIED:
        if getattr(result, name) is not False:
            raise MemoryCASOutcomeRejected("CAS observation gained authority")
        stable_result()
    _, final = inspect()
    stable_result()
    if _token_fields(final) != observed_epoch:
        raise MemoryCASOutcomeRejected("CAS observation drifted during review")
    return result
