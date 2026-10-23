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

from .contracts import MemoryRecord, MemoryScope, MemorySchemaError
from .sqlite_store import SQLiteMemoryStore, _expired, _record, _tokens


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


@dataclass(frozen=True, slots=True)
class CoherentSnapshotReview:
    read_at_ms: int
    scopes: tuple[MemoryScope, ...]
    records: tuple[tuple[MemoryRecord, ...], ...]
    provenance_sha256: str


def review_coherent_snapshot(
    store: SQLiteMemoryStore, request: CoherentSnapshotRequest
) -> CoherentSnapshotReview:
    if type(store) is not SQLiteMemoryStore or type(request) is not CoherentSnapshotRequest:
        raise TypeError("review requires exact SQLiteMemoryStore and CoherentSnapshotRequest")
    # Copy validated request carriers before a potentially reentrant clock hook.
    original = (
        request.owner_id,
        request.namespaces,
        request.text,
        request.per_namespace_limit,
        request.include_expired,
    )
    CoherentSnapshotRequest(*original)
    owner_id, namespaces, text, limit, include_expired = original
    scopes = tuple(MemoryScope(owner_id, name) for name in namespaces)
    wanted = _tokens(text)
    results: list[tuple[MemoryRecord, ...]] = []

    # SQLite transaction is anchored by its FIRST read before the clock is
    # sampled. Even if a writer commits in a clock callback or between SELECTs,
    # all namespaces observe the same pre-writer database snapshot.
    with closing(sqlite3.connect(store.path)) as conn:
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA busy_timeout=5000")
        conn.execute("BEGIN")
        conn.execute("SELECT name FROM sqlite_master ORDER BY name LIMIT 1").fetchone()
        now = store._now()
        for scope in scopes:
            rows = conn.execute(
                "SELECT * FROM memories WHERE owner_id=? AND namespace=?",
                (scope.owner_id, scope.namespace),
            ).fetchall()
            records = [_record(row) for row in rows]
            if not include_expired:
                records = [item for item in records if not _expired(item, now)]
            ranked: list[tuple[float, int, str, MemoryRecord]] = []
            for item in records:
                if wanted:
                    matched = len(wanted & _tokens(item.content))
                    if not matched:
                        continue
                    score = matched / len(wanted)
                else:
                    score = 0.0
                ranked.append((-score, -item.updated_at_ms, item.memory_id, item))
            ranked.sort(key=lambda row: row[:3])
            results.append(tuple(entry[3] for entry in ranked[:limit]))
        conn.rollback()
    if (
        request.owner_id, request.namespaces, request.text,
        request.per_namespace_limit, request.include_expired,
    ) != original:
        raise MemorySchemaError("snapshot request changed during review")

    # Only digest identity and revision metadata, never raw Memory content.
    payload = {
        "schema_version": 1,
        "owner_id": owner_id,
        "namespaces": namespaces,
        "read_at_ms": now,
        "records": [
            [
                {
                    "memory_id": row.memory_id,
                    "revision": row.revision,
                    "content_sha256": row.content_sha256,
                    "updated_at_ms": row.updated_at_ms,
                }
                for row in namespace_rows
            ]
            for namespace_rows in results
        ],
    }
    canonical = json.dumps(
        payload, ensure_ascii=False, sort_keys=True, separators=(",", ":")
    ).encode("utf-8")
    return CoherentSnapshotReview(
        now, scopes, tuple(results), hashlib.sha256(canonical).hexdigest()
    )
