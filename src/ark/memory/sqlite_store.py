"""SQLite-backed local memory with deterministic identity and fail-closed CAS."""

from __future__ import annotations

import hashlib
import json
import re
import sqlite3
import time
import unicodedata
from collections.abc import Callable
from pathlib import Path

from .contracts import (
    MemoryConflictError,
    MemoryEvent,
    MemoryQuery,
    MemoryRecord,
    MemorySchemaError,
    MemoryScope,
    MemoryWrite,
)

SCHEMA_VERSION = 1
SQLITE_INT_MAX = (1 << 63) - 1
_TOKEN_RE = re.compile(r"[A-Za-z0-9_]+|[\u3040-\u30ff\u3400-\u9fff\uff66-\uff9f]+")

_SCHEMA_V1_SQL = """CREATE TABLE memories(
                        memory_id TEXT PRIMARY KEY,
                        owner_id TEXT NOT NULL,
                        namespace TEXT NOT NULL,
                        source_id TEXT NOT NULL,
                        content TEXT NOT NULL,
                        metadata_json TEXT NOT NULL,
                        content_sha256 TEXT NOT NULL,
                        created_at_ms INTEGER NOT NULL,
                        updated_at_ms INTEGER NOT NULL,
                        expires_at_ms INTEGER,
                        revision INTEGER NOT NULL CHECK(revision>=1),
                        UNIQUE(owner_id, namespace, source_id)
                    );
                    CREATE INDEX idx_mem_scope
                    ON memories(owner_id, namespace, updated_at_ms DESC, memory_id);
                    CREATE INDEX idx_mem_expiry ON memories(expires_at_ms)
                    WHERE expires_at_ms IS NOT NULL;
                    CREATE TABLE memory_events(
                        event_id INTEGER PRIMARY KEY AUTOINCREMENT,
                        memory_id TEXT NOT NULL,
                        owner_id TEXT NOT NULL,
                        namespace TEXT NOT NULL,
                        operation TEXT NOT NULL CHECK(
                            operation IN('create','update','delete','expire')
                        ),
                        revision INTEGER NOT NULL,
                        occurred_at_ms INTEGER NOT NULL
                    );
                    CREATE INDEX idx_mem_event_scope
                    ON memory_events(owner_id, namespace, event_id);
                    PRAGMA user_version=1;"""


def _normalized_ddl(sql: str | None) -> str | None:
    """Normalize only unquoted SQL trivia; preserve quoted CHECK literals exactly."""
    if sql is None:
        return None
    output: list[str] = []
    quote: str | None = None
    index = 0
    while index < len(sql):
        char = sql[index]
        if quote is not None:
            output.append(char)
            if char == quote:
                if index + 1 < len(sql) and sql[index + 1] == quote:
                    index += 1
                    output.append(sql[index])
                else:
                    quote = None
        elif char in ("'", '"', "`"):
            quote = char
            output.append(char)
        elif not char.isspace():
            output.append(char.lower())
        index += 1
    if quote is not None:
        raise MemorySchemaError("unterminated SQLite schema quotation")
    return "".join(output)


def _schema_objects(conn: sqlite3.Connection) -> tuple[tuple[object, ...], ...]:
    rows = conn.execute(
        "SELECT type,name,tbl_name,sql FROM sqlite_master ORDER BY type,name"
    ).fetchall()
    return tuple((row[0], row[1], row[2], _normalized_ddl(row[3])) for row in rows)


def _validate_v1_schema(conn: sqlite3.Connection) -> None:
    """Fail closed on unexpected version-1 DDL, indexes, triggers or corruption.

    This is startup verification only: it does not repair existing databases,
    attest historical writers or replace independently retained evidence.
    """
    quick = conn.execute("PRAGMA quick_check").fetchall()
    if len(quick) != 1 or tuple(quick[0]) != ("ok",):
        raise MemorySchemaError("memory SQLite quick_check failed")
    with sqlite3.connect(":memory:") as expected:
        expected.executescript(_SCHEMA_V1_SQL)
        if _schema_objects(conn) != _schema_objects(expected):
            raise MemorySchemaError("memory v1 schema objects differ from frozen DDL")



def deterministic_memory_id(scope: MemoryScope, source_id: str) -> str:
    """Return a stable ID without embedding plaintext scope/source bytes."""
    if type(scope) is not MemoryScope:
        raise TypeError("scope must be an exact MemoryScope")
    if not isinstance(source_id, str) or not source_id.strip():
        raise ValueError("source_id must not be blank")
    payload = json.dumps(
        {"namespace": scope.namespace, "owner_id": scope.owner_id, "source_id": source_id},
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode()
    return "mem_" + hashlib.sha256(payload).hexdigest()


class SQLiteMemoryStore:
    """Local-only store with schema versioning, scope isolation and CAS writes."""

    def __init__(
        self,
        path: str | Path,
        *,
        clock_ms: Callable[[], int] | None = None,
    ) -> None:
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._clock_ms = clock_ms or (lambda: time.time_ns() // 1_000_000)
        self._initialize()

    def put(self, write: MemoryWrite, *, expected_revision: int = 0) -> MemoryRecord:
        if type(write) is not MemoryWrite or type(write.scope) is not MemoryScope:
            raise TypeError("write requires exact MemoryWrite and MemoryScope")
        _revision(expected_revision, allow_zero=True)
        # Pin user-controlled MemoryWrite fields before the reentrant clock.
        # Frozen dataclasses can still be modified via reflection.
        pinned_scope = write.scope
        pinned_metadata = write.metadata
        pinned_source_id = write.source_id
        pinned_content = write.content
        pinned_expiry = write.expires_at_ms
        pinned_owner = pinned_scope.owner_id
        pinned_namespace = pinned_scope.namespace
        metadata_copy = dict(pinned_metadata)
        memory_id = deterministic_memory_id(pinned_scope, pinned_source_id)
        metadata_json = json.dumps(
            metadata_copy, ensure_ascii=False, sort_keys=True, separators=(",", ":")
        )
        content_hash = hashlib.sha256(pinned_content.encode()).hexdigest()
        with self._connect() as conn:
            conn.execute("BEGIN IMMEDIATE")
            now = self._now()
            try:
                stable = (
                    write.scope is pinned_scope
                    and write.metadata is pinned_metadata
                    and (
                        pinned_scope.owner_id, pinned_scope.namespace,
                        write.source_id, write.content, write.expires_at_ms,
                        dict(write.metadata),
                    ) == (
                        pinned_owner, pinned_namespace, pinned_source_id,
                        pinned_content, pinned_expiry, metadata_copy,
                    )
                )
            except (AttributeError, TypeError, ValueError) as exc:
                raise MemorySchemaError("memory write changed during clock") from exc
            if not stable:
                raise MemorySchemaError("memory write changed during clock")
            current = conn.execute(
                "SELECT * FROM memories WHERE memory_id = ?",
                (memory_id,),
            ).fetchone()
            if current is None:
                if expected_revision != 0:
                    raise MemoryConflictError("memory does not exist at expected revision")
                revision, created = 1, now
                conn.execute(
                    """INSERT INTO memories(
                        memory_id, owner_id, namespace, source_id, content, metadata_json,
                        content_sha256, created_at_ms, updated_at_ms, expires_at_ms, revision
                    ) VALUES(?,?,?,?,?,?,?,?,?,?,?)""",
                    (
                        memory_id,
                        pinned_owner,
                        pinned_namespace,
                        pinned_source_id,
                        pinned_content,
                        metadata_json,
                        content_hash,
                        created,
                        now,
                        pinned_expiry,
                        revision,
                    ),
                )
                operation = "create"
            else:
                # Fail closed on any malformed persisted row before CAS mutation.
                # Legacy v1 valid rows remain supported without schema changes.
                stored = _record(current)
                if (stored.memory_id, stored.scope, stored.source_id) != (
                    memory_id, pinned_scope, pinned_source_id
                ):
                    raise MemorySchemaError("stored memory identity differs from write")
                actual = stored.revision
                if expected_revision != actual:
                    raise MemoryConflictError(
                        f"revision mismatch: expected {expected_revision}, actual {actual}"
                    )
                if actual == SQLITE_INT_MAX:
                    raise MemoryConflictError("memory revision exhausted SQLite INTEGER range")
                revision, created = actual + 1, stored.created_at_ms
                result = conn.execute(
                    """UPDATE memories SET
                        content=?, metadata_json=?, content_sha256=?, updated_at_ms=?,
                        expires_at_ms=?, revision=?
                    WHERE memory_id=? AND owner_id=? AND namespace=? AND revision=?""",
                    (
                        pinned_content,
                        metadata_json,
                        content_hash,
                        now,
                        pinned_expiry,
                        revision,
                        memory_id,
                        pinned_owner,
                        pinned_namespace,
                        actual,
                    ),
                )
                if result.rowcount != 1:
                    raise MemoryConflictError("memory changed during update")
                operation = "update"
            self._event(conn, memory_id, pinned_scope, operation, revision, now)
        return MemoryRecord(
            memory_id,
            pinned_scope,
            pinned_source_id,
            pinned_content,
            dict(metadata_copy),
            created,
            now,
            pinned_expiry,
            revision,
            content_hash,
        )

    def get(
        self,
        memory_id: str,
        scope: MemoryScope,
        *,
        include_expired: bool = False,
    ) -> MemoryRecord | None:
        _memory_id(memory_id)
        if type(scope) is not MemoryScope:
            raise TypeError("scope must be an exact MemoryScope")
        if type(include_expired) is not bool:
            raise TypeError("include_expired must be a bool")
        # Bind both the database read and its expiry clock to the same read
        # transaction; reject scope retargeting by a reentrant clock callback.
        pinned_scope = MemoryScope(scope.owner_id, scope.namespace)
        with self._connect() as conn:
            conn.execute("BEGIN")
            row = conn.execute(
                """SELECT * FROM memories
                WHERE memory_id=? AND owner_id=? AND namespace=?""",
                (memory_id, pinned_scope.owner_id, pinned_scope.namespace),
            ).fetchone()
            if row is None:
                return None
            record = _record(row)
            now = self._now() if not include_expired else None
            if (scope.owner_id, scope.namespace) != (
                pinned_scope.owner_id, pinned_scope.namespace
            ):
                raise MemorySchemaError("memory get scope changed during clock")
            if now is not None and _expired(record, now):
                return None
            return record

    def search(self, query: MemoryQuery) -> list[MemoryRecord]:
        if type(query) is not MemoryQuery or type(query.scope) is not MemoryScope:
            raise TypeError("query requires exact MemoryQuery and MemoryScope")
        # Pin the full query, not only its scope. Frozen query fields can be
        # changed by a reflected mutation while the injected clock executes.
        original_scope = query.scope
        pinned_scope = MemoryScope(original_scope.owner_id, original_scope.namespace)
        pinned_text = query.text
        pinned_limit = query.limit
        pinned_include_expired = query.include_expired
        MemoryQuery(pinned_scope, pinned_text, pinned_limit, pinned_include_expired)
        with self._connect() as conn:
            conn.execute("BEGIN")
            # The SELECT anchors the SQLite snapshot before the clock. A
            # concurrent writer in the clock callback cannot mix epochs.
            rows = conn.execute(
                "SELECT * FROM memories WHERE owner_id=? AND namespace=?",
                (pinned_scope.owner_id, pinned_scope.namespace),
            ).fetchall()
            now = self._now()
            if (
                query.scope is not original_scope
                or type(query.scope) is not MemoryScope
                or (query.scope.owner_id, query.scope.namespace)
                != (pinned_scope.owner_id, pinned_scope.namespace)
                or query.text != pinned_text
                or query.limit != pinned_limit
                or query.include_expired != pinned_include_expired
            ):
                raise MemorySchemaError("memory search query changed during clock")
            records = [_record(row) for row in rows]
            if not pinned_include_expired:
                records = [item for item in records if not _expired(item, now)]
            wanted = _tokens(pinned_text)
            ranked: list[tuple[float, int, str, MemoryRecord]] = []
            for item in records:
                if wanted:
                    matched = len(wanted & _tokens(item.content))
                    if matched == 0:
                        continue
                    score = matched / len(wanted)
                else:
                    score = 0.0
                ranked.append((-score, -item.updated_at_ms, item.memory_id, item))
            ranked.sort(key=lambda value: value[:3])
            return [value[3] for value in ranked[:pinned_limit]]

    def delete(self, memory_id: str, scope: MemoryScope, *, expected_revision: int) -> bool:
        _memory_id(memory_id)
        _revision(expected_revision, allow_zero=False)
        if type(scope) is not MemoryScope:
            raise TypeError("scope must be an exact MemoryScope")
        # A clock callback may reflectively modify a frozen scope object.
        # Bind both SQL and audit events to one pre-clock identity epoch.
        pinned_scope = MemoryScope(scope.owner_id, scope.namespace)
        with self._connect() as conn:
            conn.execute("BEGIN IMMEDIATE")
            now = self._now()
            if (
                scope.owner_id, scope.namespace
            ) != (pinned_scope.owner_id, pinned_scope.namespace):
                raise MemorySchemaError("memory delete scope changed during clock")
            row = conn.execute(
                """SELECT * FROM memories
                WHERE memory_id=? AND owner_id=? AND namespace=?""",
                (memory_id, pinned_scope.owner_id, pinned_scope.namespace),
            ).fetchone()
            if row is None:
                return False
            stored = _record(row)
            if stored.memory_id != memory_id or stored.scope != pinned_scope:
                raise MemorySchemaError("stored memory identity differs from delete")
            actual = stored.revision
            if actual != expected_revision:
                raise MemoryConflictError(
                    f"revision mismatch: expected {expected_revision}, actual {actual}"
                )
            result = conn.execute(
                """DELETE FROM memories
                WHERE memory_id=? AND owner_id=? AND namespace=? AND revision=?""",
                (memory_id, pinned_scope.owner_id, pinned_scope.namespace, expected_revision),
            )
            if result.rowcount != 1:
                raise MemoryConflictError("memory changed during delete")
            self._event(conn, memory_id, pinned_scope, "delete", actual, now)
        return True

    def purge_expired(self, *, scope: MemoryScope | None = None) -> int:
        if scope is not None and type(scope) is not MemoryScope:
            raise TypeError("scope must be an exact MemoryScope")
        pinned_scope = (
            MemoryScope(scope.owner_id, scope.namespace) if scope is not None else None
        )
        # Claim the SQLite writer slot before taking either the clock reading
        # or the expiry snapshot. A read-before-write transaction permits a
        # concurrent refresh to resurrect a selected row before deletion.
        with self._connect() as conn:
            conn.execute("BEGIN IMMEDIATE")
            now = self._now()
            if scope is not None and (
                scope.owner_id, scope.namespace
            ) != (pinned_scope.owner_id, pinned_scope.namespace):
                raise MemorySchemaError("memory purge scope changed during clock")
            if pinned_scope is None:
                rows = conn.execute(
                    """SELECT * FROM memories
                    WHERE expires_at_ms IS NOT NULL AND expires_at_ms<=? ORDER BY memory_id""",
                    (now,),
                ).fetchall()
            else:
                rows = conn.execute(
                    """SELECT * FROM memories
                    WHERE owner_id=? AND namespace=? AND expires_at_ms IS NOT NULL
                    AND expires_at_ms<=? ORDER BY memory_id""",
                    (pinned_scope.owner_id, pinned_scope.namespace, now),
                ).fetchall()
            for row in rows:
                stored = _record(row)
                if pinned_scope is not None and stored.scope != pinned_scope:
                    raise MemorySchemaError("stored memory scope differs from expiry query")
                # Bind deletion to the exact row/scope/revision/expiry predicate
                # observed under the lock. Only actual deletions emit events.
                deleted = conn.execute(
                    """DELETE FROM memories
                    WHERE memory_id=? AND owner_id=? AND namespace=?
                    AND revision=? AND expires_at_ms IS NOT NULL AND expires_at_ms<=?""",
                    (
                        stored.memory_id, stored.scope.owner_id, stored.scope.namespace,
                        stored.revision, now,
                    ),
                )
                if deleted.rowcount != 1:
                    raise MemoryConflictError("expired memory changed before delete")
                self._event(
                    conn, stored.memory_id, stored.scope, "expire",
                    stored.revision, now,
                )
        return len(rows)

    def events(
        self,
        scope: MemoryScope,
        *,
        after_event_id: int = 0,
        limit: int = 100,
    ) -> list[MemoryEvent]:
        if type(scope) is not MemoryScope:
            raise TypeError("scope must be an exact MemoryScope")
        if type(after_event_id) is not int or not 0 <= after_event_id <= SQLITE_INT_MAX:
            raise ValueError("after_event_id must be a non-negative integer")
        if type(limit) is not int or not 1 <= limit <= 1000:
            raise ValueError("limit must be an integer from 1 to 1000")
        with self._connect() as conn:
            rows = conn.execute(
                """SELECT * FROM memory_events
                WHERE owner_id=? AND namespace=? AND event_id>?
                ORDER BY event_id LIMIT ?""",
                (scope.owner_id, scope.namespace, after_event_id, limit),
            ).fetchall()
        # Event rows have no associated source_id after deletion, so validate
        # canonical shape and scope, not an unverifiable source-id preimage.
        # V1 permits clocks to move backwards between independent memories:
        # ordering is by event_id only, never by occurred_at_ms.
        result: list[MemoryEvent] = []
        previous_id = after_event_id
        for row in rows:
            def stored_int(event_row: sqlite3.Row, column: str, *, minimum: int) -> int:
                value = event_row[column]
                if type(value) is not int or value < minimum:
                    raise MemorySchemaError(f"stored event {column} is not a valid INTEGER")
                return value

            def stored_text(event_row: sqlite3.Row, column: str) -> str:
                value = event_row[column]
                if type(value) is not str:
                    raise MemorySchemaError(f"stored event {column} must be TEXT")
                return value

            event_id = stored_int(row, "event_id", minimum=1)
            revision = stored_int(row, "revision", minimum=1)
            occurred = stored_int(row, "occurred_at_ms", minimum=0)
            memory_id = stored_text(row, "memory_id")
            owner_id = stored_text(row, "owner_id")
            namespace = stored_text(row, "namespace")
            operation = stored_text(row, "operation")
            if event_id <= previous_id:
                raise MemorySchemaError("stored event IDs are not strictly increasing")
            previous_id = event_id
            try:
                _memory_id(memory_id)
                recorded_scope = MemoryScope(owner_id, namespace)
            except (ValueError, TypeError) as exc:
                raise MemorySchemaError("stored event identity or scope is invalid") from exc
            if recorded_scope != scope:
                raise MemorySchemaError("stored event scope does not match query")
            if operation not in {"create", "update", "delete", "expire"}:
                raise MemorySchemaError("stored event operation is invalid")
            result.append(
                MemoryEvent(event_id, memory_id, recorded_scope, operation, revision, occurred)
            )
        return result

    def _initialize(self) -> None:
        with self._connect() as conn:
            # executescript() issues an implicit COMMIT and can preserve a
            # partially created v1 database after a verification failure.
            # Reserve the writer slot before checking version/emptiness.
            conn.execute("BEGIN IMMEDIATE")
            version = int(conn.execute("PRAGMA user_version").fetchone()[0])
            if version < 0:
                raise MemorySchemaError(f"unsupported negative memory schema version {version}")
            if version > SCHEMA_VERSION:
                raise MemorySchemaError(
                    f"memory database schema {version} is newer than supported {SCHEMA_VERSION}"
                )
            if version == 0:
                existing = conn.execute(
                    "SELECT name FROM sqlite_master WHERE name NOT LIKE 'sqlite_%' LIMIT 1"
                ).fetchone()
                if existing is not None:
                    raise MemorySchemaError("unversioned memory database is not empty")
                # V1's frozen DDL consists of semicolon-separated statements;
                # execute one at a time *inside* the existing transaction.
                for statement in _SCHEMA_V1_SQL.split(";"):
                    if statement.strip():
                        conn.execute(statement)
            _validate_v1_schema(conn)

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.path)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA journal_mode=WAL")
        conn.execute("PRAGMA busy_timeout=5000")
        return conn

    def _now(self) -> int:
        value = self._clock_ms()
        if type(value) is not int or not 0 <= value <= SQLITE_INT_MAX:
            raise ValueError("clock_ms must return a non-negative integer")
        return value

    @staticmethod
    def _event(
        conn: sqlite3.Connection,
        memory_id: str,
        scope: MemoryScope,
        operation: str,
        revision: int,
        occurred_at_ms: int,
    ) -> None:
        conn.execute(
            """INSERT INTO memory_events(
                memory_id,owner_id,namespace,operation,revision,occurred_at_ms
            ) VALUES(?,?,?,?,?,?)""",
            (
                memory_id,
                scope.owner_id,
                scope.namespace,
                operation,
                revision,
                occurred_at_ms,
            ),
        )


def _record(row: sqlite3.Row) -> MemoryRecord:
    """Reject tampered on-disk identity, digests and storage classes on reads.

    This does not attest the writer or verify an independent history root.
    It preserves the existing v1 schema and the current public record contract.
    """
    def stored_text(column: str) -> str:
        value = row[column]
        if type(value) is not str:
            raise MemorySchemaError(f"stored {column} must be SQLite TEXT")
        return value

    def stored_int(column: str, *, nullable: bool = False) -> int | None:
        value = row[column]
        if value is None and nullable:
            return None
        if type(value) is not int or value < 0:
            raise MemorySchemaError(f"stored {column} must be non-negative SQLite INTEGER")
        return value

    owner_id = stored_text("owner_id")
    namespace = stored_text("namespace")
    source_id = stored_text("source_id")
    memory_id = stored_text("memory_id")
    content = stored_text("content")
    content_sha = stored_text("content_sha256")
    metadata_json = stored_text("metadata_json")
    created = stored_int("created_at_ms")
    updated = stored_int("updated_at_ms")
    expires = stored_int("expires_at_ms", nullable=True)
    revision = stored_int("revision")
    if revision is None or revision < 1:
        raise MemorySchemaError("stored revision must be a positive integer")
    try:
        scope = MemoryScope(owner_id, namespace)
        expected_id = deterministic_memory_id(scope, source_id)
    except (TypeError, ValueError) as exc:
        raise MemorySchemaError("stored memory scope or source is invalid") from exc
    if memory_id != expected_id:
        raise MemorySchemaError("stored memory identity digest does not match")
    if content_sha != hashlib.sha256(content.encode()).hexdigest():
        raise MemorySchemaError("stored memory content digest does not match")
    try:
        metadata = json.loads(metadata_json)
    except (TypeError, ValueError) as exc:
        raise MemorySchemaError("stored metadata JSON is invalid") from exc
    if not isinstance(metadata, dict) or not all(
        type(k) is str and type(v) is str for k, v in metadata.items()
    ):
        raise MemorySchemaError("stored metadata is not an exact string mapping")
    canonical = json.dumps(
        metadata, ensure_ascii=False, sort_keys=True, separators=(",", ":")
    )
    if canonical != metadata_json:
        raise MemorySchemaError("stored metadata is not canonical JSON")
    return MemoryRecord(
        memory_id, scope, source_id, content, metadata, created, updated,
        expires, revision, content_sha,
    )


def _expired(record: MemoryRecord, now: int) -> bool:
    return record.expires_at_ms is not None and record.expires_at_ms <= now


def _memory_id(value: object) -> None:
    if not isinstance(value, str) or re.fullmatch(r"mem_[0-9a-f]{64}", value) is None:
        raise ValueError("memory_id must be a canonical deterministic memory ID")


def _revision(value: object, *, allow_zero: bool) -> None:
    minimum = 0 if allow_zero else 1
    if type(value) is not int or not minimum <= value <= SQLITE_INT_MAX:
        raise ValueError(f"expected_revision must be an integer >= {minimum}")


def _tokens(text: str) -> set[str]:
    normalized = unicodedata.normalize("NFKC", text).casefold()
    result: set[str] = set()
    for match in _TOKEN_RE.finditer(normalized):
        chunk = match.group(0)
        result.add(chunk)
        if any(
            "\u3040" <= char <= "\u30ff"
            or "\u3400" <= char <= "\u9fff"
            or "\uff66" <= char <= "\uff9f"
            for char in chunk
        ) and len(chunk) >= 2:
            result.update(chunk[i : i + 2] for i in range(len(chunk) - 1))
    return result
