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
from types import MappingProxyType

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
_ORIGINAL_HASHLIB = hashlib
_ORIGINAL_JSON = json
_ORIGINAL_SHA256 = hashlib.sha256
_ORIGINAL_DUMPS = json.dumps
_ORIGINAL_EVENT_DOMAIN = _EVENT_DOMAIN
_ORIGINAL_ROW_DOMAIN = _ROW_DOMAIN


def _require_original_generation_digest() -> None:
    """Deny replaced local digest dependencies before private SQLite access.

    This only protects in-process callback identities. It does not provide
    authenticated writer provenance or an external immutable witness.
    """
    if (
        hashlib is not _ORIGINAL_HASHLIB or json is not _ORIGINAL_JSON
        or hashlib.sha256 is not _ORIGINAL_SHA256
        or json.dumps is not _ORIGINAL_DUMPS
        or _EVENT_DOMAIN is not _ORIGINAL_EVENT_DOMAIN
        or _ROW_DOMAIN is not _ORIGINAL_ROW_DOMAIN
    ):
        raise MemoryGenerationCASRejected("generation CAS digest dependencies changed")



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
_ORIGINAL_TOKEN_INIT = vars(_TOKEN_TYPE)["__init__"]
_TOKEN_FIELDS = (
    "memory_id", "create_event_id", "last_event_id", "revision",
    "event_prefix_sha256", "row_sha256",
)
_ORIGINAL_TOKEN_FIELDS = tuple(
    vars(_TOKEN_TYPE)[name] for name in _TOKEN_FIELDS
)
_TOKEN_HOOKS = ("__new__", "__getattribute__", "__getattr__")
_ORIGINAL_TOKEN_HOOKS = tuple(
    vars(_TOKEN_TYPE).get(name) for name in _TOKEN_HOOKS
)
_ORIGINAL_TOKEN_DENIALS = tuple(
    vars(_TOKEN_TYPE)[name] for name in _TOKEN_DENIALS
)


def _require_original_token_denials() -> None:
    _require_original_generation_digest()
    if (
        MemoryGenerationCASToken is not _TOKEN_TYPE
        or vars(_TOKEN_TYPE).get("__init__") is not _ORIGINAL_TOKEN_INIT
        or any(
            vars(_TOKEN_TYPE).get(name) is not original
            for name, original in zip(
                _TOKEN_FIELDS, _ORIGINAL_TOKEN_FIELDS, strict=True,
            )
        )
        or any(
            vars(_TOKEN_TYPE).get(name) is not original
            for name, original in zip(
                _TOKEN_HOOKS, _ORIGINAL_TOKEN_HOOKS, strict=True,
            )
        )
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


# The opt-in generation-CAS path must not read caller-owned frozen dataclass
# fields through a replaced class-level slot/getter. This pins only the new
# optional API's inputs; frozen Memory v1 contracts and schema stay untouched.
_SCOPE_TYPE = MemoryScope
_WRITE_TYPE = MemoryWrite
_SCOPE_FIELDS = ("owner_id", "namespace")
_WRITE_FIELDS = ("scope", "source_id", "content", "metadata", "expires_at_ms")
# Exact scoped row comparisons must not invoke swapped equality/hash hooks
# before the caller's private local history has been validated.
_INPUT_HOOKS = (
    "__init__", "__post_init__", "__new__", "__getattribute__",
    "__getattr__", "__eq__", "__hash__",
)
_ORIGINAL_SCOPE_FIELDS = tuple(
    vars(_SCOPE_TYPE)[name] for name in _SCOPE_FIELDS
)
_ORIGINAL_WRITE_FIELDS = tuple(
    vars(_WRITE_TYPE)[name] for name in _WRITE_FIELDS
)
_ORIGINAL_SCOPE_HOOKS = tuple(
    vars(_SCOPE_TYPE).get(name) for name in _INPUT_HOOKS
)
_ORIGINAL_WRITE_HOOKS = tuple(
    vars(_WRITE_TYPE).get(name) for name in _INPUT_HOOKS
)


def _require_original_generation_inputs() -> None:
    if MemoryScope is not _SCOPE_TYPE or MemoryWrite is not _WRITE_TYPE:
        raise MemoryGenerationCASRejected("generation input carrier changed")
    for cls, names, originals in (
        (_SCOPE_TYPE, _SCOPE_FIELDS, _ORIGINAL_SCOPE_FIELDS),
        (_WRITE_TYPE, _WRITE_FIELDS, _ORIGINAL_WRITE_FIELDS),
        (_SCOPE_TYPE, _INPUT_HOOKS, _ORIGINAL_SCOPE_HOOKS),
        (_WRITE_TYPE, _INPUT_HOOKS, _ORIGINAL_WRITE_HOOKS),
    ):
        if any(
            vars(cls).get(name) is not original
            for name, original in zip(names, originals, strict=True)
        ):
            raise MemoryGenerationCASRejected("generation input carrier descriptor changed")


def _require_bounded_source_id(source_id: object) -> None:
    """Limit opt-in CAS identities by actual UTF-8 bytes, not code points.

    Frozen Memory v1 accepts up to 512 characters. The stricter, optional
    generation-CAS path must not treat a multibyte identifier as a bounded
    512-byte identity or let unpaired surrogates escape as encoding errors.
    """
    if type(source_id) is not str or not source_id.strip():
        raise MemoryGenerationCASRejected("exact nonblank generation source required")
    # Preserve the original cheap character cap before any UTF-8 allocation.
    # A direct observation caller is not required to construct MemoryWrite.
    if len(source_id) > 512:
        raise MemoryGenerationCASRejected(
            "generation source exceeds 512 UTF-8 bytes"
        )
    try:
        size = len(source_id.encode("utf-8", errors="strict"))
    except UnicodeEncodeError as exc:
        raise MemoryGenerationCASRejected(
            "generation source is not valid UTF-8"
        ) from exc
    if size > 512:
        raise MemoryGenerationCASRejected(
            "generation source exceeds 512 UTF-8 bytes"
        )



def _require_bounded_scope(scope: MemoryScope) -> None:
    """Validate opt-in generation identities without changing frozen Memory v1.

    Legacy MemoryScope is character-bounded; generation CAS requires exact,
    well-formed and byte-bounded UTF-8 identifiers before hashing or SQLite.
    """
    _require_original_generation_inputs()
    if type(scope) is not MemoryScope:
        raise MemoryGenerationCASRejected("exact generation scope required")
    for name in ("owner_id", "namespace"):
        value = getattr(scope, name)
        if type(value) is not str or not value.strip() or len(value) > 256:
            raise MemoryGenerationCASRejected("exact bounded generation scope required")
        try:
            size = len(value.encode("utf-8", errors="strict"))
        except UnicodeEncodeError as exc:
            raise MemoryGenerationCASRejected(
                "generation scope is not valid UTF-8"
            ) from exc
        if size > 256:
            raise MemoryGenerationCASRejected(
                "generation scope exceeds 256 UTF-8 bytes"
            )



def _digest(domain: bytes, fields: object) -> str:
    _require_original_generation_digest()
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
    # This helper is also consumed by independent read-only reconciliation.
    # Inspect original slots before reading any caller-retained token field.
    _require_original_token_denials()
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
    # sqlite_sequence.name is not UNIQUE. fetchone() could accept a
    # valid-looking first marker while a second forged marker remains.
    # Snapshot the *entire* marker set before any row is interpreted or
    # any generation-fenced WRITE is admitted.
    sequences = conn.execute(
        "SELECT seq FROM sqlite_sequence WHERE name='memory_events'"
    ).fetchall()
    if (
        type(count) is not int or count < 0
        or (
            count == 0 and (
                first is not None or last is not None or sequences
            )
        )
        or (
            count > 0 and (
                type(first) is not int or first != 1
                or type(last) is not int or last != count
                or last > SQLITE_INT_MAX
                or len(sequences) != 1
                or type(sequences[0][0]) is not int
                or sequences[0][0] != last
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
    # Both digest computations may invoke synthetic reentrant hooks. Do
    # not execute a substituted dataclass constructor after those callbacks.
    event_digest = _digest(_EVENT_DOMAIN, exact_events)
    row_digest = _row_hash(record)
    _require_original_token_denials()
    result = _TOKEN_TYPE(
        memory_id, create_id, previous_id, rev, event_digest, row_digest,
    )
    _require_original_token_denials()
    _token_fields(result)
    return record, result


def observe_memory_generation_for_cas(
    store: SQLiteMemoryStore,
    scope: MemoryScope,
    source_id: str,
) -> MemoryGenerationCASToken:
    """Read one coherent row/history snapshot; return no write permission."""
    _require_original_generation_digest()
    _require_original_generation_inputs()
    if (
        type(store) is not SQLiteMemoryStore
        or type(scope) is not MemoryScope
    ):
        raise MemoryGenerationCASRejected("exact generation observation inputs required")
    _require_original_token_denials()
    _require_bounded_scope(scope)
    _require_bounded_source_id(source_id)
    # Pin the original owner/namespace/path *before* the first identity
    # digest. A reentrant hashing callback must not replace the caller's
    # input with a fresh (even equal-valued) custody epoch and then have that
    # replacement accepted as the baseline for private SQLite reads.
    owner, namespace, path = scope.owner_id, scope.namespace, store.path

    def stable() -> None:
        _require_original_generation_inputs()
        _require_original_token_denials()
        if (
            store.path is not path or scope.owner_id is not owner
            or scope.namespace is not namespace
        ):
            raise MemoryGenerationCASRejected("generation observation input changed")

    stable()
    memory_id = deterministic_memory_id(scope, source_id)
    stable()
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
    _require_original_generation_digest()
    _require_original_generation_inputs()
    if (
        type(store) is not SQLiteMemoryStore
        or type(write) is not MemoryWrite
        or type(write.scope) is not MemoryScope
    ):
        raise MemoryGenerationCASRejected("exact Memory generation write inputs required")
    _require_original_token_denials()
    _require_bounded_scope(write.scope)
    _require_bounded_source_id(write.source_id)
    pinned_token = _token_fields(retained)
    original_scope = write.scope
    original_owner, original_namespace = write.scope.owner_id, write.scope.namespace
    original_source, original_content = write.source_id, write.content
    original_metadata, original_expiry = write.metadata, write.expires_at_ms
    original_path = store.path
    # MemoryWrite's constructor normalized these fields, but callers can
    # reflectively replace frozen slots after construction. Reject malformed
    # proposals before hashing identities or opening private SQLite. Frozen
    # Memory v1 remains unchanged; this is only the opt-in CAS path.
    if (
        type(original_content) is not str
        or not original_content.strip()
        or len(original_content) > 1_000_000
    ):
        raise MemoryGenerationCASRejected(
            "generation CAS requires exact bounded content"
        )
    if original_expiry is not None and (
        type(original_expiry) is not int
        or not 0 <= original_expiry <= SQLITE_INT_MAX
    ):
        raise MemoryGenerationCASRejected(
            "generation CAS requires SQLite-range expiry"
        )
    if (
        type(original_metadata) not in (dict, MappingProxyType)
        or len(original_metadata) > 64
    ):
        raise MemoryGenerationCASRejected(
            "generation CAS requires bounded plain metadata"
        )
    metadata = dict(original_metadata)
    if any(
        type(key) is not str or not key.strip() or len(key) > 4096
        or type(value) is not str or len(value) > 4096
        for key, value in metadata.items()
    ):
        raise MemoryGenerationCASRejected(
            "generation CAS requires bounded string metadata"
        )
    expected_id = deterministic_memory_id(original_scope, original_source)
    if pinned_token[0] != expected_id:
        raise MemoryConflictError("generation token does not match target identity")
    metadata_json = json.dumps(
        metadata, ensure_ascii=False, sort_keys=True, separators=(",", ":"),
    )
    # Memory v1's string length check does not reject unpaired surrogates.
    # Fail closed *before* opening a write transaction: SQLite cannot encode
    # such text, and raw UnicodeEncodeError is not an opt-in CAS diagnosis.
    try:
        metadata_json.encode("utf-8", errors="strict")
        content_bytes = original_content.encode("utf-8", errors="strict")
    except UnicodeEncodeError as exc:
        raise MemoryGenerationCASRejected(
            "generation CAS payload is not valid UTF-8"
        ) from exc
    content_hash = hashlib.sha256(content_bytes).hexdigest()

    def stable() -> None:
        _require_original_generation_inputs()
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
