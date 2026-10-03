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
_TOKEN_RE = re.compile(r"[A-Za-z0-9_]+|[\u3040-\u30ff\u3400-\u9fff\uff66-\uff9f]+")


def deterministic_memory_id(scope: MemoryScope, source_id: str) -> str:
    """Return a stable ID without embedding plaintext scope/source bytes."""
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
        _revision(expected_revision, allow_zero=True)
        memory_id = deterministic_memory_id(write.scope, write.source_id)
        now = self._now()
        metadata_json = json.dumps(
            dict(write.metadata), ensure_ascii=False, sort_keys=True, separators=(",", ":")
        )
        content_hash = hashlib.sha256(write.content.encode()).hexdigest()
        with self._connect() as conn:
            current = conn.execute(
                "SELECT revision, created_at_ms FROM memories WHERE memory_id = ?",
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
                        write.scope.owner_id,
                        write.scope.namespace,
                        write.source_id,
                        write.content,
                        metadata_json,
                        content_hash,
                        created,
                        now,
                        write.expires_at_ms,
                        revision,
                    ),
                )
                operation = "create"
            else:
                actual = int(current["revision"])
                if expected_revision != actual:
                    raise MemoryConflictError(
                        f"revision mismatch: expected {expected_revision}, actual {actual}"
                    )
                revision, created = actual + 1, int(current["created_at_ms"])
                result = conn.execute(
                    """UPDATE memories SET
                        content=?, metadata_json=?, content_sha256=?, updated_at_ms=?,
                        expires_at_ms=?, revision=?
                    WHERE memory_id=? AND owner_id=? AND namespace=? AND revision=?""",
                    (
                        write.content,
                        metadata_json,
                        content_hash,
                        now,
                        write.expires_at_ms,
                        revision,
                        memory_id,
                        write.scope.owner_id,
                        write.scope.namespace,
                        actual,
                    ),
                )
                if result.rowcount != 1:
                    raise MemoryConflictError("memory changed during update")
                operation = "update"
            self._event(conn, memory_id, write.scope, operation, revision, now)
        return MemoryRecord(
            memory_id,
            write.scope,
            write.source_id,
            write.content,
            dict(write.metadata),
            created,
            now,
            write.expires_at_ms,
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
        if type(include_expired) is not bool:
            raise TypeError("include_expired must be a bool")
        with self._connect() as conn:
            row = conn.execute(
                """SELECT * FROM memories
                WHERE memory_id=? AND owner_id=? AND namespace=?""",
                (memory_id, scope.owner_id, scope.namespace),
            ).fetchone()
        if row is None:
            return None
        record = _record(row)
        if not include_expired and _expired(record, self._now()):
            return None
        return record

    def search(self, query: MemoryQuery) -> list[MemoryRecord]:
        now = self._now()
        with self._connect() as conn:
            rows = conn.execute(
                "SELECT * FROM memories WHERE owner_id=? AND namespace=?",
                (query.scope.owner_id, query.scope.namespace),
            ).fetchall()
        records = [_record(row) for row in rows]
        if not query.include_expired:
            records = [item for item in records if not _expired(item, now)]
        wanted = _tokens(query.text)
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
        return [value[3] for value in ranked[: query.limit]]

    def delete(self, memory_id: str, scope: MemoryScope, *, expected_revision: int) -> bool:
        _memory_id(memory_id)
        _revision(expected_revision, allow_zero=False)
        now = self._now()
        with self._connect() as conn:
            row = conn.execute(
                """SELECT revision FROM memories
                WHERE memory_id=? AND owner_id=? AND namespace=?""",
                (memory_id, scope.owner_id, scope.namespace),
            ).fetchone()
            if row is None:
                return False
            actual = int(row["revision"])
            if actual != expected_revision:
                raise MemoryConflictError(
                    f"revision mismatch: expected {expected_revision}, actual {actual}"
                )
            result = conn.execute(
                """DELETE FROM memories
                WHERE memory_id=? AND owner_id=? AND namespace=? AND revision=?""",
                (memory_id, scope.owner_id, scope.namespace, expected_revision),
            )
            if result.rowcount != 1:
                raise MemoryConflictError("memory changed during delete")
            self._event(conn, memory_id, scope, "delete", actual, now)
        return True

    def purge_expired(self, *, scope: MemoryScope | None = None) -> int:
        now = self._now()
        with self._connect() as conn:
            if scope is None:
                rows = conn.execute(
                    """SELECT memory_id,owner_id,namespace,revision FROM memories
                    WHERE expires_at_ms IS NOT NULL AND expires_at_ms<=? ORDER BY memory_id""",
                    (now,),
                ).fetchall()
            else:
                rows = conn.execute(
                    """SELECT memory_id,owner_id,namespace,revision FROM memories
                    WHERE owner_id=? AND namespace=? AND expires_at_ms IS NOT NULL
                    AND expires_at_ms<=? ORDER BY memory_id""",
                    (scope.owner_id, scope.namespace, now),
                ).fetchall()
            for row in rows:
                record_scope = MemoryScope(row["owner_id"], row["namespace"])
                conn.execute("DELETE FROM memories WHERE memory_id=?", (row["memory_id"],))
                self._event(
                    conn,
                    row["memory_id"],
                    record_scope,
                    "expire",
                    int(row["revision"]),
                    now,
                )
        return len(rows)

    def events(
        self,
        scope: MemoryScope,
        *,
        after_event_id: int = 0,
        limit: int = 100,
    ) -> list[MemoryEvent]:
        if type(after_event_id) is not int or after_event_id < 0:
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
        return [
            MemoryEvent(
                int(row["event_id"]),
                row["memory_id"],
                MemoryScope(row["owner_id"], row["namespace"]),
                row["operation"],
                int(row["revision"]),
                int(row["occurred_at_ms"]),
            )
            for row in rows
        ]

    def _initialize(self) -> None:
        with self._connect() as conn:
            version = int(conn.execute("PRAGMA user_version").fetchone()[0])
            if version > SCHEMA_VERSION:
                raise MemorySchemaError(
                    f"memory database schema {version} is newer than supported {SCHEMA_VERSION}"
                )
            if version == 0:
                conn.executescript(
                    """CREATE TABLE memories(
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
                )

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.path)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA journal_mode=WAL")
        conn.execute("PRAGMA busy_timeout=5000")
        return conn

    def _now(self) -> int:
        value = self._clock_ms()
        if type(value) is not int or value < 0:
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
    metadata = json.loads(row["metadata_json"])
    if not isinstance(metadata, dict) or not all(
        isinstance(k, str) and isinstance(v, str) for k, v in metadata.items()
    ):
        raise MemorySchemaError("stored metadata is not a string mapping")
    return MemoryRecord(
        row["memory_id"],
        MemoryScope(row["owner_id"], row["namespace"]),
        row["source_id"],
        row["content"],
        metadata,
        int(row["created_at_ms"]),
        int(row["updated_at_ms"]),
        None if row["expires_at_ms"] is None else int(row["expires_at_ms"]),
        int(row["revision"]),
        row["content_sha256"],
    )


def _expired(record: MemoryRecord, now: int) -> bool:
    return record.expires_at_ms is not None and record.expires_at_ms <= now


def _memory_id(value: object) -> None:
    if not isinstance(value, str) or re.fullmatch(r"mem_[0-9a-f]{64}", value) is None:
        raise ValueError("memory_id must be a canonical deterministic memory ID")


def _revision(value: object, *, allow_zero: bool) -> None:
    minimum = 0 if allow_zero else 1
    if type(value) is not int or value < minimum:
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
