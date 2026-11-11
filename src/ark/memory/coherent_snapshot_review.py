"""Read-only coherent multi-namespace Memory v1 review (no personal-data connector).

This opt-in review uses a single SQLite read transaction and one clock sample.
Its content-free digest is local continuity metadata, not provenance attestation
or action authority; the existing v1 schema and public store API are unchanged.
"""

from __future__ import annotations

import hashlib
import json
import sqlite3
from contextlib import closing
from dataclasses import dataclass
from pathlib import Path

from .contracts import MemoryRecord, MemorySchemaError, MemoryScope
from .sqlite_store import (
    SQLiteMemoryStore,
    _expired,
    _record,
    _require_safe_memory_path,
    _tokens,
    _validate_v1_schema,
)

_MAX_NAMESPACE_SCAN_ROWS = 10_000


@dataclass(frozen=True, slots=True)
class CoherentSnapshotRequest:
    owner_id: str
    namespaces: tuple[str, ...]
    text: str = ""
    per_namespace_limit: int = 10
    include_expired: bool = False

    def __post_init__(self) -> None:
        if type(self.owner_id) is not str:
            raise TypeError("owner_id must be an exact string")
        if type(self.namespaces) is not tuple or not 1 <= len(self.namespaces) <= 16:
            raise ValueError("namespaces must be an exact tuple with 1..16 entries")
        if any(type(name) is not str for name in self.namespaces):
            raise TypeError("namespace values must be exact strings")
        if len(set(self.namespaces)) != len(self.namespaces):
            raise ValueError("namespaces must be unique")
        for name in self.namespaces:
            MemoryScope(self.owner_id, name)
        if type(self.text) is not str or len(self.text) > 4096:
            raise ValueError("text must be an exact string of <=4096 characters")
        if (
            type(self.per_namespace_limit) is not int
            or not 1 <= self.per_namespace_limit <= 100
        ):
            raise ValueError("per_namespace_limit must be an exact integer 1..100")
        if type(self.include_expired) is not bool:
            raise TypeError("include_expired must be an exact boolean")
        # Reject ill-formed Unicode before opening Memory or reading private
        # rows. Otherwise a lone surrogate can survive tokenization and fail
        # much later in the query digest after a full SQLite snapshot scan.
        try:
            self.owner_id.encode("utf-8", errors="strict")
            self.text.encode("utf-8", errors="strict")
            for namespace in self.namespaces:
                namespace.encode("utf-8", errors="strict")
        except UnicodeError as exc:
            raise ValueError(
                "snapshot request text must be UTF-8 encodable"
            ) from exc


@dataclass(frozen=True, slots=True)
class CoherentSnapshotReview:
    read_at_ms: int
    scopes: tuple[MemoryScope, ...]
    records: tuple[tuple[MemoryRecord, ...], ...]
    provenance_sha256: str


# Request reconstruction is a validation step, but a monkeypatched dataclass
# initializer/post-init is executable code. Keep its import-original identity
# before calling it; an exact request instance is not sufficient protection.
_REQUEST_TYPE = CoherentSnapshotRequest
_ORIGINAL_REQUEST_INIT = vars(_REQUEST_TYPE)["__init__"]
_ORIGINAL_REQUEST_POST_INIT = vars(_REQUEST_TYPE)["__post_init__"]
_REQUEST_FIELDS = (
    "owner_id", "namespaces", "text", "per_namespace_limit", "include_expired",
)
_ORIGINAL_REQUEST_FIELDS = tuple(vars(_REQUEST_TYPE)[name] for name in _REQUEST_FIELDS)
_REQUEST_HOOKS = ("__new__", "__getattribute__", "__getattr__")
_ORIGINAL_REQUEST_HOOKS = tuple(
    vars(_REQUEST_TYPE).get(name) for name in _REQUEST_HOOKS
)


def _require_original_request_validator() -> None:
    if (
        CoherentSnapshotRequest is not _REQUEST_TYPE
        or vars(_REQUEST_TYPE).get("__init__") is not _ORIGINAL_REQUEST_INIT
        or vars(_REQUEST_TYPE).get("__post_init__") is not _ORIGINAL_REQUEST_POST_INIT
        or any(
            vars(_REQUEST_TYPE).get(name) is not original
            for name, original in zip(_REQUEST_FIELDS, _ORIGINAL_REQUEST_FIELDS, strict=True)
        )
        or any(
            vars(_REQUEST_TYPE).get(name) is not original
            for name, original in zip(_REQUEST_HOOKS, _ORIGINAL_REQUEST_HOOKS, strict=True)
        )
    ):
        raise MemorySchemaError("memory snapshot request validator changed")


# Pin the result type independently of a reentrant synthetic constructor hook.
_COHERENT_SNAPSHOT_RESULT_TYPE = CoherentSnapshotReview
_ORIGINAL_COHERENT_SNAPSHOT_INIT = vars(_COHERENT_SNAPSHOT_RESULT_TYPE)["__init__"]
_RESULT_FIELDS = ("read_at_ms", "scopes", "records", "provenance_sha256")
_ORIGINAL_RESULT_FIELDS = tuple(
    vars(_COHERENT_SNAPSHOT_RESULT_TYPE)[name] for name in _RESULT_FIELDS
)
_RESULT_HOOKS = ("__new__", "__getattribute__", "__getattr__")
_ORIGINAL_RESULT_HOOKS = tuple(
    vars(_COHERENT_SNAPSHOT_RESULT_TYPE).get(name) for name in _RESULT_HOOKS
)


def _require_original_snapshot_result_constructor() -> None:
    # A counterfeit constructor can execute arbitrary Python before the
    # postconstruction result-type/authority review ever runs.
    if (
        CoherentSnapshotReview is not _COHERENT_SNAPSHOT_RESULT_TYPE
        or vars(_COHERENT_SNAPSHOT_RESULT_TYPE).get("__init__")
        is not _ORIGINAL_COHERENT_SNAPSHOT_INIT
        or any(
            vars(_COHERENT_SNAPSHOT_RESULT_TYPE).get(name) is not original
            for name, original in zip(_RESULT_FIELDS, _ORIGINAL_RESULT_FIELDS, strict=True)
        )
        or any(
            vars(_COHERENT_SNAPSHOT_RESULT_TYPE).get(name) is not original
            for name, original in zip(_RESULT_HOOKS, _ORIGINAL_RESULT_HOOKS, strict=True)
        )
    ):
        raise MemorySchemaError("memory snapshot result constructor changed")


def review_coherent_snapshot(
    store: SQLiteMemoryStore, request: CoherentSnapshotRequest
) -> CoherentSnapshotReview:
    if type(store) is not SQLiteMemoryStore or type(request) is not CoherentSnapshotRequest:
        raise TypeError("review requires exact SQLiteMemoryStore and CoherentSnapshotRequest")
    _require_original_snapshot_result_constructor()
    _require_original_request_validator()
    # Copy validated request carriers before a potentially reentrant clock hook.
    original = (
        request.owner_id,
        request.namespaces,
        request.text,
        request.per_namespace_limit,
        request.include_expired,
    )
    _require_original_request_validator()
    _REQUEST_TYPE(*original)
    _require_original_request_validator()
    owner_id, namespaces, text, limit, include_expired = original
    scopes = tuple(MemoryScope(owner_id, name) for name in namespaces)
    results: list[tuple[MemoryRecord, ...]] = []
    path_epoch = store.path
    if not isinstance(path_epoch, Path):
        raise MemorySchemaError("memory snapshot requires a stable Path source")

    # The request and per-namespace scopes are independent mutable carriers
    # under Python reflection even though their dataclasses are frozen.
    # Check BETWEEN phases, not just at return: a later callback could undo
    # an earlier drift and make an end-only comparison appear unchanged.
    request_epoch = tuple((type(value), value) for value in original)
    scope_epoch = tuple(
        (scope, type(scope), scope.owner_id, scope.namespace) for scope in scopes
    )
    record_epochs: list[tuple[MemoryRecord, tuple[object, ...]]] = []

    def assert_epoch() -> None:
        # Every database, clock and digest callback may rebind a request slot.
        # Inspect class descriptors BEFORE reading any retained request field.
        _require_original_request_validator()
        if store.path is not path_epoch:
            raise MemorySchemaError("memory snapshot source path changed during review")
        current = (
            request.owner_id, request.namespaces, request.text,
            request.per_namespace_limit, request.include_expired,
        )
        if (
            request.namespaces is not namespaces
            or tuple((type(value), value) for value in current) != request_epoch
            or any(
                value is not original_carrier
                for value, (_, original_carrier) in zip(
                    current, request_epoch, strict=True,
                )
            )
        ):
            raise MemorySchemaError("snapshot request changed during review")
        if any(
            type(scope) is not scope_type
            or type(scope.owner_id) is not str
            or type(scope.namespace) is not str
            or scope.owner_id is not owner
            or scope.namespace is not namespace
            for scope, scope_type, owner, namespace in scope_epoch
        ):
            raise MemorySchemaError("memory snapshot scope changed during review")

    def record_epoch(record: MemoryRecord) -> tuple[object, ...]:
        fields = (
            record.memory_id, record.source_id, record.content,
            record.created_at_ms, record.updated_at_ms, record.expires_at_ms,
            record.revision, record.content_sha256,
            record.scope.owner_id, record.scope.namespace,
        )
        return (
            # Keep the actual nested carriers alive. Storing only id(scope)
            # or metadata's value digest permits equal-valued replacements
            # after hydration and before content-free snapshot construction.
            record.scope,
            record.metadata,
            tuple((type(value), value) for value in fields),
            (type(record.metadata), tuple(sorted(dict(record.metadata).items()))),
            fields,
        )

    def assert_record_epochs() -> None:
        for record, epoch in record_epochs:
            if type(record) is not MemoryRecord:
                raise MemorySchemaError("memory snapshot record changed during review")
            current = record_epoch(record)
            if (
                current[0] is not epoch[0]
                or current[1] is not epoch[1]
                or current[2:4] != epoch[2:4]
                or any(
                    value is not original
                    for value, original in zip(current[4], epoch[4], strict=True)
                )
            ):
                raise MemorySchemaError("memory snapshot record changed during review")

    def metadata_digest(record: MemoryRecord) -> str:
        # Metadata hashing is a callback boundary too. Do not allow a later
        # record's hash to conceal temporary mutation of an earlier record.
        assert_epoch()
        assert_record_epochs()
        digest = hashlib.sha256(
            json.dumps(
                dict(record.metadata), ensure_ascii=False, sort_keys=True,
                separators=(",", ":"),
            ).encode("utf-8")
        ).hexdigest()
        assert_epoch()
        assert_record_epochs()
        return digest

    assert_epoch()
    wanted = _tokens(text)
    assert_epoch()

    # SQLite transaction is anchored by its FIRST read before the clock is
    # sampled. Even if a writer commits in a clock callback or between SELECTs,
    # all namespaces observe the same pre-writer database snapshot.
    # Read-only diagnostics must not create an empty replacement database
    # if the configured store file vanished after initialization.
    try:
        # Path resolution and URI construction are separate input boundaries:
        # reject reflected request/source changes BEFORE opening any handle.
        # The store checked this filename at initialization, but an alias
        # can be installed later. Never follow a symbolic/hardlinked Memory
        # database or unsafe SQLite sidecar during a private multi-scope read.
        # These path checks are local preflights, not atomic dirfd custody.
        _require_safe_memory_path(path_epoch, create=False)
        assert_epoch()
        resolved_path = path_epoch.resolve()
        assert_epoch()
        _require_safe_memory_path(path_epoch, create=False)
        assert_epoch()
        readonly_uri = resolved_path.as_uri() + "?mode=ro"
        assert_epoch()
        snapshot_connection = sqlite3.connect(readonly_uri, uri=True)
    except sqlite3.DatabaseError as exc:
        raise MemorySchemaError("cannot open memory snapshot read-only") from exc
    with closing(snapshot_connection) as conn:
        # Connection creation may be substituted in synthetic fault fixtures.
        # Refuse drift before the FIRST SELECT, not after schema callbacks.
        assert_epoch()
        conn.row_factory = sqlite3.Row
        assert_epoch()
        conn.execute("PRAGMA busy_timeout=5000")
        assert_epoch()
        conn.execute("BEGIN")
        assert_epoch()
        conn.execute("SELECT name FROM sqlite_master ORDER BY name LIMIT 1").fetchone()
        assert_epoch()
        # Revalidate frozen Memory v1 DDL inside the SAME pinned read snapshot.
        # A store that was healthy during __init__ can be modified later.
        # Neither a matching row hash nor successful SELECT * proves that its
        # SQL schema, indexes, triggers and declared version are unchanged.
        version = conn.execute("PRAGMA user_version").fetchone()[0]
        assert_epoch()
        if version != 1:
            raise MemorySchemaError("memory snapshot schema version changed")
        try:
            _validate_v1_schema(conn)
        except sqlite3.DatabaseError as exc:
            raise MemorySchemaError("memory snapshot schema cannot be verified") from exc
        assert_epoch()
        now = store._now()
        assert_epoch()
        for scope in scopes:
            assert_epoch()
            cursor = conn.execute(
                "SELECT * FROM memories WHERE owner_id=? AND namespace=?",
                (scope.owner_id, scope.namespace),
            )
            # The ranking must consider every candidate in a namespace, but
            # untrusted stores must not force unbounded Python hydration.
            rows = cursor.fetchmany(_MAX_NAMESPACE_SCAN_ROWS + 1)
            assert_epoch()
            if len(rows) > _MAX_NAMESPACE_SCAN_ROWS:
                raise MemorySchemaError("memory snapshot row scan budget exceeded")
            records = []
            for row in rows:
                record = _record(row)
                assert_epoch()
                record_epochs.append((record, record_epoch(record)))
                records.append(record)
                assert_record_epochs()
            if not include_expired:
                # Expiry predicates are a Python callback boundary, too.
                # A later predicate must not be able to restore an earlier
                # record/scope mutation before ranking and hide the drift.
                live_records: list[MemoryRecord] = []
                for item in records:
                    assert_epoch()
                    assert_record_epochs()
                    expired = _expired(item, now)
                    assert_epoch()
                    assert_record_epochs()
                    if not expired:
                        live_records.append(item)
                records = live_records
            ranked: list[tuple[float, int, str, MemoryRecord]] = []
            for item in records:
                assert_epoch()
                assert_record_epochs()
                if wanted:
                    matched = len(wanted & _tokens(item.content))
                    assert_epoch()
                    assert_record_epochs()
                    if not matched:
                        continue
                    score = matched / len(wanted)
                else:
                    score = 0.0
                ranked.append((-score, -item.updated_at_ms, item.memory_id, item))
            assert_epoch()
            assert_record_epochs()
            ranked.sort(key=lambda row: row[:3])
            results.append(tuple(entry[3] for entry in ranked[:limit]))
            assert_epoch()
            assert_record_epochs()
        conn.rollback()
    assert_epoch()
    assert_record_epochs()

    # Query hashing is also a reentrant Python boundary. Recheck its input
    # epoch immediately, before later metadata/JSON callbacks can restore
    # a temporarily retargeted request, source, or previously read record.
    query_digest = hashlib.sha256(text.encode("utf-8")).hexdigest()
    assert_epoch()
    assert_record_epochs()

    # Only digest identity and revision metadata, never raw Memory content.
    payload = {
        "schema_version": 1,
        "witness_format_version": 2,
        "owner_id": owner_id,
        "namespaces": namespaces,
        "read_at_ms": now,
        # Bind selection intent, not only the returned records. The raw query
        # is deliberately absent from the content-free witness payload.
        "query_sha256": query_digest,
        "per_namespace_limit": limit,
        "include_expired": include_expired,
        "records": [
            [
                {
                    "memory_id": row.memory_id,
                    "revision": row.revision,
                    "content_sha256": row.content_sha256,
                    "metadata_sha256": metadata_digest(row),
                    "created_at_ms": row.created_at_ms,
                    "updated_at_ms": row.updated_at_ms,
                    "expires_at_ms": row.expires_at_ms,
                }
                for row in namespace_rows
            ]
            for namespace_rows in results
        ],
    }
    canonical = json.dumps(
        payload, ensure_ascii=False, sort_keys=True, separators=(",", ":")
    ).encode("utf-8")
    # Serialization and hashing are separate reentrant callback boundaries.
    # A transient retarget during JSON encoding must not be masked by a
    # subsequent hash callback that restores the original input carriers.
    assert_epoch()
    assert_record_epochs()
    digest = hashlib.sha256(canonical).hexdigest()
    # SHA-256 hooks may also mutate the request, source or hydrated rows.
    # Refuse a stale but apparently well-formed witness after final hashing.
    assert_epoch()
    assert_record_epochs()
    # Result construction is the final callback boundary: a fixture hook can
    # mutate the original request, source or hydrated rows, or forge the
    # detached result itself after the content-free digest was computed.
    detached_records = tuple(results)
    _require_original_snapshot_result_constructor()
    review = _COHERENT_SNAPSHOT_RESULT_TYPE(now, scopes, detached_records, digest)
    _require_original_snapshot_result_constructor()
    assert_epoch()
    assert_record_epochs()
    if (
        type(review) is not _COHERENT_SNAPSHOT_RESULT_TYPE
        or type(review.read_at_ms) is not int
        or review.read_at_ms is not now
        or review.scopes is not scopes
        or review.records is not detached_records
        or review.provenance_sha256 is not digest
    ):
        raise MemorySchemaError("memory snapshot result changed during review")
    return review
