"""Opt-in generation-fenced SQLite CAS update for an existing Memory v1 row.

The frozen Memory v1 put/delete API and SQLite schema are unchanged. This
explicit API pins a locally observed lifetime (create event ID), event prefix,
and row image, then checks all three *inside the same BEGIN IMMEDIATE write
transaction* that advances the row and appends its update event.

A token is not consent, a writer identity, a trusted clock, or a capability.
This operation only mutates the specified local Memory v1 SQLite database.
"""

from __future__ import annotations

import hashlib
import json
import re
import sqlite3
from contextlib import closing
from dataclasses import dataclass

from .contracts import (
    MemoryConflictError,
    MemoryRecord,
    MemorySchemaError,
    MemoryScope,
    MemoryWrite,
)
from .sqlite_store import (
    SQLITE_INT_MAX,
    SQLiteMemoryStore,
    _record,
    _validate_v1_schema,
    deterministic_memory_id,
)

_MAX_EVENTS = 40_000
_SHA = re.compile(r"[0-9a-f]{64}\Z")
_EVENT_DOMAIN = b"ARK-memory-generation-write-event-prefix-v1\0"
_ROW_DOMAIN = b"ARK-memory-generation-write-row-v1\0"


class MemoryGenerationCASRejected(MemorySchemaError):
    """An opt-in lifetime-fenced update cannot safely be attempted."""


@dataclass(frozen=True, slots=True)
class MemoryGenerationCASToken:
    memory_id: str
    create_event_id: int
    last_event_id: int
    revision: int
    event_prefix_sha256: str
    row_sha256: str

    @property
    def external_action_authorized(self) -> bool:
        return False

    @property
    def consent_authenticated(self) -> bool:
        return False


# Bind deny-only token authority to its import-time implementation. Capturing
# descriptors only after a caller has entered the SQLite path would accept a
# preinstalled False-returning replacement as the trusted baseline.
_TOKEN_DENIALS = ("external_action_authorized", "consent_authenticated")
_TOKEN_TYPE = MemoryGenerationCASToken
_ORIGINAL_TOKEN_DENIALS = tuple(
    vars(_TOKEN_TYPE)[name] for name in _TOKEN_DENIALS
)


def _require_original_token_denials() -> None:
    if (
        MemoryGenerationCASToken is not _TOKEN_TYPE
        or any(
            vars(_TOKEN_TYPE).get(name) is not original
            for name, original in zip(
                _TOKEN_DENIALS, _ORIGINAL_TOKEN_DENIALS, strict=True,
            )
        )
    ):
        raise MemoryGenerationCASRejected(
            "generation token or denial epoch changed"
        )


def _digest(domain: bytes, fields: object) -> str:
    return hashlib.sha256(
        domain + json.dumps(
            fields, sort_keys=True, separators=(",", ":"), ensure_ascii=True,
            allow_nan=False,
        ).encode("ascii")
    ).hexdigest()


def _row_hash(record: MemoryRecord) -> str:
    return _digest(_ROW_DOMAIN, (
        record.memory_id, record.scope.owner_id, record.scope.namespace,
        record.source_id, record.content, tuple(sorted(record.metadata.items())),
        record.created_at_ms, record.updated_at_ms, record.expires_at_ms,
        record.revision, record.content_sha256,
    ))


def _token_fields(token: MemoryGenerationCASToken) -> tuple[object, ...]:
    if type(token) is not MemoryGenerationCASToken:
        raise MemoryGenerationCASRejected("exact Memory generation token required")
    fields = (
        token.memory_id, token.create_event_id, token.last_event_id,
        token.revision, token.event_prefix_sha256, token.row_sha256,
    )
    if (
        type(fields[0]) is not str
        or re.fullmatch(r"mem_[0-9a-f]{64}", fields[0]) is None
        or any(type(value) is not int or not 1 <= value <= SQLITE_INT_MAX
               for value in fields[1:4])
        or fields[1] > fields[2]
        or any(type(value) is not str or _SHA.fullmatch(value) is None
               for value in fields[4:])
    ):
        raise MemoryGenerationCASRejected("noncanonical generation token")
    return fields


def _snapshot(
    conn: sqlite3.Connection,
    memory_id: str,
    scope: MemoryScope,
    source_id: str,
) -> tuple[MemoryRecord, MemoryGenerationCASToken]:
    _validate_v1_schema(conn)
    # The per-row CAS prefix cannot by itself detect deletion of events
    # belonging to another row. Check the complete local append high-water
    # in this SAME transaction before interpreting the row's generation.
    # This is corruption detection, not authenticated event custody.
    count, first, last = conn.execute(
        "SELECT COUNT(*),MIN(event_id),MAX(event_id) FROM memory_events"
    ).fetchone()
    sequence = conn.execute(
        "SELECT seq FROM sqlite_sequence WHERE name='memory_events'"
    ).fetchone()
    if (
        type(count) is not int or count < 0
        or (
            count == 0 and (
                first is not None or last is not None or sequence is not None
            )
        )
        or (
            count > 0 and (
                type(first) is not int or first != 1
                or type(last) is not int or last != count
                or last > SQLITE_INT_MAX
                or sequence is None
                or type(sequence[0]) is not int
                or sequence[0] != last
            )
        )
    ):
        raise MemoryGenerationCASRejected(
            "Memory generation global event high-water mismatch"
        )
    row = conn.execute("SELECT * FROM memories WHERE memory_id=?", (memory_id,)).fetchone()
    if row is None:
        raise MemoryConflictError("generation-fenced update requires an existing row")
    record = _record(row)
    if (
        record.memory_id != memory_id
        or record.scope != scope
        or record.source_id != source_id
    ):
        raise MemoryGenerationCASRejected("Memory generation row identity changed")

    events = conn.execute(
        "SELECT event_id,owner_id,namespace,operation,revision,occurred_at_ms "
        "FROM memory_events WHERE memory_id=? ORDER BY event_id LIMIT ?",
        (memory_id, _MAX_EVENTS + 1),
    ).fetchall()
    if not events or len(events) > _MAX_EVENTS:
        raise MemoryGenerationCASRejected("Memory generation history absent or unbounded")

    alive = False
    rev = 0
    create_id = 0
    created_at = None
    updated_at = None
    previous_id = 0
    exact_events: list[tuple[int, str, str, str, int, int]] = []
    for event in events:
        event_id, owner, namespace, operation, revision, at = tuple(event)
        if (
            type(event_id) is not int or not previous_id < event_id <= SQLITE_INT_MAX
            or type(owner) is not str or type(namespace) is not str
            or (owner, namespace) != (scope.owner_id, scope.namespace)
            or type(operation) is not str
            or type(revision) is not int or not 1 <= revision <= SQLITE_INT_MAX
            or type(at) is not int or not 0 <= at <= SQLITE_INT_MAX
        ):
            raise MemoryGenerationCASRejected("Memory generation event identity invalid")
        if updated_at is not None and at < updated_at:
            raise MemoryGenerationCASRejected(
                "Memory generation event clock moved backward"
            )
        if operation == "create":
            if alive or revision != 1:
                raise MemoryGenerationCASRejected("Memory generation create sequence invalid")
            alive, rev, create_id, created_at = True, 1, event_id, at
        elif operation == "update":
            if not alive or rev == SQLITE_INT_MAX or revision != rev + 1:
                raise MemoryGenerationCASRejected("Memory generation update sequence invalid")
            rev = revision
        elif operation in ("delete", "expire"):
            if not alive or revision != rev:
                raise MemoryGenerationCASRejected("Memory generation terminal sequence invalid")
            alive = False
        else:
            raise MemoryGenerationCASRejected("Memory generation operation invalid")
        previous_id, updated_at = event_id, at
        exact_events.append((event_id, owner, namespace, operation, revision, at))
    if (
        not alive or create_id <= 0 or rev != record.revision
        or created_at != record.created_at_ms
        or updated_at != record.updated_at_ms
    ):
        raise MemoryGenerationCASRejected("Memory generation row/event mismatch")
    result = MemoryGenerationCASToken(
        memory_id, create_id, previous_id, rev,
        _digest(_EVENT_DOMAIN, exact_events), _row_hash(record),
    )
    _token_fields(result)
    return record, result


def observe_memory_generation_for_cas(
    store: SQLiteMemoryStore,
    scope: MemoryScope,
    source_id: str,
) -> MemoryGenerationCASToken:
    """Read one coherent row/history snapshot; return no write permission."""
    if (
        type(store) is not SQLiteMemoryStore
        or type(scope) is not MemoryScope
        or type(source_id) is not str or not source_id.strip() or len(source_id) > 512
    ):
        raise MemoryGenerationCASRejected("exact generation observation inputs required")
    _require_original_token_denials()
    owner, namespace, path = scope.owner_id, scope.namespace, store.path
    memory_id = deterministic_memory_id(scope, source_id)

    def stable() -> None:
        _require_original_token_denials()
        if (
            store.path is not path or scope.owner_id is not owner
            or scope.namespace is not namespace
        ):
            raise MemoryGenerationCASRejected("generation observation input changed")

    try:
        stable()
        with closing(store._connect_readonly()) as conn:
            conn.execute("BEGIN")
            stable()
            _, token = _snapshot(conn, memory_id, scope, source_id)
            stable()
    except sqlite3.Error as exc:
        raise MemoryGenerationCASRejected("generation observation SQLite unavailable") from exc
    stable()
    fields = _token_fields(token)
    denied = _TOKEN_DENIALS
    descriptors = _ORIGINAL_TOKEN_DENIALS
    _require_original_token_denials()

    def stable_token() -> None:
        stable()
        if (
            type(token) is not MemoryGenerationCASToken
            or any(now is not original for now, original in zip(
                _token_fields(token), fields, strict=True,
            ))
            or any(getattr(MemoryGenerationCASToken, key) is not descriptor
                   for key, descriptor in zip(
                       denied, descriptors, strict=True,
                   ))
        ):
            raise MemoryGenerationCASRejected("generation token or denial epoch changed")

    stable_token()
    for name in denied:
        if getattr(token, name) is not False:
            raise MemoryGenerationCASRejected("generation token gained authority")
        # False-valued properties can still mutate the token or replace
        # previously inspected vetoes. A CAS token never becomes permission.
        stable_token()
    return token


def generation_fenced_memory_update(
    store: SQLiteMemoryStore,
    write: MemoryWrite,
    *,
    retained: MemoryGenerationCASToken,
) -> MemoryRecord:
    """Atomically reject stale-generation CAS and update one existing v1 row.

    After an ambiguous commit/connection error, callers must inspect locally;
    this function never retries an update or treats the token as consent.
    """
    if (
        type(store) is not SQLiteMemoryStore
        or type(write) is not MemoryWrite
        or type(write.scope) is not MemoryScope
    ):
        raise MemoryGenerationCASRejected("exact Memory generation write inputs required")
    _require_original_token_denials()
    pinned_token = _token_fields(retained)
    original_scope = write.scope
    original_owner, original_namespace = write.scope.owner_id, write.scope.namespace
    original_source, original_content = write.source_id, write.content
    original_metadata, original_expiry = write.metadata, write.expires_at_ms
    original_path = store.path
    metadata = dict(original_metadata)
    expected_id = deterministic_memory_id(original_scope, original_source)
    if pinned_token[0] != expected_id:
        raise MemoryConflictError("generation token does not match target identity")
    metadata_json = json.dumps(
        metadata, ensure_ascii=False, sort_keys=True, separators=(",", ":"),
    )
    content_hash = hashlib.sha256(original_content.encode()).hexdigest()

    def stable() -> None:
        _require_original_token_denials()
        if (
            store.path is not original_path
            or write.scope is not original_scope
            or write.metadata is not original_metadata
            or write.source_id is not original_source
            or write.content is not original_content
            or write.expires_at_ms is not original_expiry
            or original_scope.owner_id is not original_owner
            or original_scope.namespace is not original_namespace
            or dict(write.metadata) != metadata
            or any(
                current is not original for current, original in zip(
                    _token_fields(retained), pinned_token, strict=True,
                )
            )
        ):
            raise MemoryGenerationCASRejected("generation CAS inputs changed")

    stable()
    try:
        with closing(store._connect()) as conn, conn:
            conn.execute("BEGIN IMMEDIATE")
            stable()
            current, fresh = _snapshot(conn, expected_id, original_scope, original_source)
            stable()
            if _token_fields(fresh) != pinned_token:
                raise MemoryConflictError("memory generation changed since retained CAS")
            if current.revision == SQLITE_INT_MAX:
                raise MemoryConflictError("memory revision exhausted")
            now = store._now()
            stable()
            # Never revive an expired row or persist a newly expired value.
            # This is a local clock sanity guard, NOT trusted-clock authorization.
            if now < current.updated_at_ms:
                raise MemoryConflictError("generation CAS clock regressed")
            if current.expires_at_ms is not None and now >= current.expires_at_ms:
                raise MemoryConflictError("generation CAS source expired")
            if original_expiry is not None and now >= original_expiry:
                raise MemoryGenerationCASRejected(
                    "generation CAS proposed expiry is not future"
                )
            # A revision token is not permission to relax a retention deadline.
            # Until a separate consent/retention gate is proven, never extend
            # or clear an already finite expiry, even before its deadline.
            if current.expires_at_ms is not None and (
                original_expiry is None or original_expiry > current.expires_at_ms
            ):
                raise MemoryGenerationCASRejected(
                    "generation CAS expiry extension needs independent authorization"
                )
            revision = current.revision + 1
            changed = conn.execute(
                "UPDATE memories SET content=?,metadata_json=?,content_sha256=?,"
                "updated_at_ms=?,expires_at_ms=?,revision=? "
                "WHERE memory_id=? AND owner_id=? AND namespace=? AND revision=?",
                (
                    original_content, metadata_json, content_hash,
                    now, original_expiry, revision,
                    expected_id, original_owner, original_namespace, current.revision,
                ),
            )
            if changed.rowcount != 1:
                raise MemoryConflictError("generation CAS row changed during update")
            store._event(conn, expected_id, original_scope, "update", revision, now)
            stable()
            updated, updated_token = _snapshot(
                conn, expected_id, original_scope, original_source,
            )
            stable()
            if (
                updated.revision != revision
                or updated.content != original_content
                or dict(updated.metadata) != metadata
                or updated.expires_at_ms != original_expiry
                or updated.updated_at_ms != now
                or updated.content_sha256 != content_hash
                or updated_token.create_event_id != fresh.create_event_id
                or updated_token.last_event_id <= fresh.last_event_id
                or updated_token.event_prefix_sha256 == fresh.event_prefix_sha256
            ):
                raise MemoryGenerationCASRejected("generation CAS postwrite invariant failed")
            stable()
            # Pin the *result* as well as caller inputs before connection
            # __exit__ can durably COMMIT and invoke synthetic callbacks.
            # A post-COMMIT result rewrite must never be returned as truth.
            updated_epoch = (
                updated.memory_id, updated.scope, updated.source_id,
                updated.content, updated.created_at_ms, updated.updated_at_ms,
                updated.expires_at_ms, updated.revision, updated.content_sha256,
                updated.metadata,
            )
            updated_metadata = dict(updated.metadata)
            updated_token_epoch = _token_fields(updated_token)
    except sqlite3.Error as exc:
        raise MemoryGenerationCASRejected("generation CAS SQLite outcome uncertain") from exc
    # COMMIT happened. A later rejection never proves rollback or permits retry.
    stable()
    try:
        result_intact = (
            type(updated) is MemoryRecord
            and all(now is prior for now, prior in zip(
                (
                    updated.memory_id, updated.scope, updated.source_id,
                    updated.content, updated.created_at_ms, updated.updated_at_ms,
                    updated.expires_at_ms, updated.revision, updated.content_sha256,
                    updated.metadata,
                ), updated_epoch, strict=True,
            ))
            and dict(updated.metadata) == updated_metadata
            and all(now is prior for now, prior in zip(
                _token_fields(updated_token), updated_token_epoch, strict=True,
            ))
            and _row_hash(updated) == updated_token_epoch[5]
        )
    except (TypeError, ValueError, AttributeError) as exc:
        raise MemoryGenerationCASRejected(
            "generation CAS post-COMMIT result uncertain; manual review required"
        ) from exc
    if not result_intact:
        raise MemoryGenerationCASRejected(
            "generation CAS post-COMMIT result uncertain; manual review required"
        )
    stable()

    # The post-COMMIT carrier may agree with its in-transaction snapshot even
    # when a synthetic callback or concurrent writer has changed the actual
    # persisted Memory row/event chain. Re-open a fresh READ transaction; do
    # not claim this is an atomic cross-process or trusted custody proof.
    # A failed verification is UNKNOWN/manual review, never a retry signal.
    try:
        with closing(store._connect_readonly()) as readonly:
            readonly.execute("BEGIN")
            stable()
            observed, observed_token = _snapshot(
                readonly, expected_id, original_scope, original_source,
            )
            stable()
            if (
                type(observed) is not MemoryRecord
                or _token_fields(observed_token) != updated_token_epoch
                or _row_hash(observed) != updated_token_epoch[5]
            ):
                raise MemoryGenerationCASRejected(
                    "generation CAS post-COMMIT persisted state differs"
                )
            readonly.commit()
    except (sqlite3.Error, MemoryConflictError, MemorySchemaError) as exc:
        raise MemoryGenerationCASRejected(
            "generation CAS post-COMMIT readback uncertain; manual review required"
        ) from exc
    stable()
    # Readback itself is an untrusted callback boundary. Recheck exact
    # result carriers (not just a value-equal row digest) before returning.
    try:
        still_intact = (
            type(updated) is MemoryRecord
            and all(now is prior for now, prior in zip(
                (
                    updated.memory_id, updated.scope, updated.source_id,
                    updated.content, updated.created_at_ms, updated.updated_at_ms,
                    updated.expires_at_ms, updated.revision, updated.content_sha256,
                    updated.metadata,
                ), updated_epoch, strict=True,
            ))
            and dict(updated.metadata) == updated_metadata
            and _row_hash(updated) == updated_token_epoch[5]
            and all(now is prior for now, prior in zip(
                _token_fields(updated_token), updated_token_epoch, strict=True,
            ))
        )
    except (TypeError, ValueError, AttributeError) as exc:
        raise MemoryGenerationCASRejected(
            "generation CAS post-COMMIT readback result changed; manual review required"
        ) from exc
    if not still_intact:
        raise MemoryGenerationCASRejected(
            "generation CAS post-COMMIT readback result changed; manual review required"
        )
    stable()
    return updated
