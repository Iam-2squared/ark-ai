"""Disconnected, read-only audit history continuity diagnostics.

The digest chain validates local SQLite continuity against a separately retained
witness. It is NOT external provenance, clock attestation, an authorization
ledger, or an exactly-once backend execution guarantee.
"""

from __future__ import annotations

import hashlib
import json
import re
import sqlite3
from contextlib import closing
from dataclasses import dataclass

from .audit import SQLiteActionAudit, _validate_v1_schema
from .contracts import ActionAuditSchemaError

_GENESIS = hashlib.sha256(b"ark-synthetic-action-audit-v1").digest()
_HEX = re.compile(r"[0-9a-f]{64}")


@dataclass(frozen=True, slots=True)
class AuditContinuityWitness:
    event_count: int
    tail_event_id: int
    chain_sha256: str

    def __post_init__(self) -> None:
        if type(self.event_count) is not int or self.event_count < 0:
            raise ValueError("event_count must be a nonnegative exact integer")
        if type(self.tail_event_id) is not int or self.tail_event_id < 0:
            raise ValueError("tail_event_id must be a nonnegative exact integer")
        if type(self.chain_sha256) is not str or _HEX.fullmatch(self.chain_sha256) is None:
            raise ValueError("chain_sha256 must be a canonical lowercase digest")
        if (self.event_count == 0) != (self.tail_event_id == 0):
            raise ValueError("empty audit witness must have zero tail identity")


def _row_payload(row: sqlite3.Row, *, previous_id: int) -> tuple[int, bytes]:
    event_id = row["event_id"]
    occurred = row["occurred_at_ms"]
    if type(event_id) is not int or event_id <= previous_id:
        raise ActionAuditSchemaError("audit event ID must be increasing SQLite INTEGER")
    if type(occurred) is not int or occurred < 0:
        raise ActionAuditSchemaError("audit timestamp must be nonnegative SQLite INTEGER")
    values: dict[str, str] = {}
    for field in ("request_id", "tool", "capability", "scope", "arguments_sha256", "outcome"):
        value = row[field]
        if type(value) is not str or not value.strip():
            raise ActionAuditSchemaError(f"audit field {field} must be nonempty SQLite TEXT")
        values[field] = value
    if (
        re.fullmatch(r"act_[0-9a-f]{64}", values["request_id"]) is None
        or _HEX.fullmatch(values["arguments_sha256"]) is None
    ):
        raise ActionAuditSchemaError("audit event digest identity is invalid")
    payload = {
        "event_id": event_id,
        "occurred_at_ms": occurred,
        **values,
    }
    encoded = json.dumps(
        payload, ensure_ascii=False, sort_keys=True, separators=(",", ":")
    ).encode("utf-8")
    return event_id, encoded


def review_audit_continuity(
    audit: SQLiteActionAudit,
    *,
    retained: AuditContinuityWitness | None = None,
    max_events: int = 10_000,
    require_monotonic_time: bool = False,
) -> AuditContinuityWitness:
    """Read a coherent prefix with optional caller-clock rollback diagnosis.

    Ordering supplied timestamps does not authenticate the clock or event.
    """
    if type(audit) is not SQLiteActionAudit:
        raise TypeError("audit must be an exact SQLiteActionAudit")
    if type(max_events) is not int or not 1 <= max_events <= 10_000:
        raise ValueError("max_events must be an exact integer from 1 to 10000")
    if type(require_monotonic_time) is not bool:
        raise TypeError("require_monotonic_time must be an exact boolean")
    if retained is not None and type(retained) is not AuditContinuityWitness:
        raise TypeError("retained witness must be an exact AuditContinuityWitness")
    pinned = None
    if retained is not None:
        pinned = (retained.event_count, retained.tail_event_id, retained.chain_sha256)

    # A short read transaction pins all event rows to the same SQLite snapshot.
    # Do not issue PRAGMA journal_mode on ordinary read-only diagnostics.
    try:
        # The reviewer must never create a new empty database when the
        # configured audit file is missing, even on a stale audit object.
        with closing(
            sqlite3.connect(audit.path.resolve().as_uri() + "?mode=ro", uri=True)
        ) as conn:
            conn.row_factory = sqlite3.Row
            conn.execute("PRAGMA busy_timeout=5000")
            conn.execute("BEGIN")
            # An audit object may outlive an on-disk schema replacement.
            # Validate the exact v1 structure inside the same read snapshot.
            version = conn.execute("PRAGMA user_version").fetchone()[0]
            if type(version) is not int or version != 1:
                raise ActionAuditSchemaError("audit review requires exact schema version 1")
            _validate_v1_schema(conn)
            rows = conn.execute(
                """SELECT event_id,request_id,tool,capability,scope,arguments_sha256,
                          outcome,occurred_at_ms
                FROM action_events ORDER BY event_id LIMIT ?""",
                (max_events + 1,),
            ).fetchall()
            conn.rollback()
    except sqlite3.DatabaseError as exc:
        raise ActionAuditSchemaError("cannot read audit snapshot") from exc
    if len(rows) > max_events:
        raise ActionAuditSchemaError("audit review budget exceeded")

    chain = _GENESIS
    count = 0
    tail = 0
    previous_at = -1
    if pinned is not None and pinned[0] == 0:
        if pinned[1:] != (0, _GENESIS.hex()):
            raise ActionAuditSchemaError("retained empty audit witness differs")
    for row in rows:
        tail, payload = _row_payload(row, previous_id=tail)
        at_ms = row["occurred_at_ms"]
        if require_monotonic_time and at_ms < previous_at:
            raise ActionAuditSchemaError("audit event clock regressed")
        previous_at = at_ms
        chain = hashlib.sha256(chain + b"\n" + payload).digest()
        count += 1
        if pinned is not None and count == pinned[0]:
            if (tail, chain.hex()) != pinned[1:]:
                raise ActionAuditSchemaError("retained audit prefix differs")
    if pinned is not None and count < pinned[0]:
        raise ActionAuditSchemaError("audit history is shorter than retained witness")
    if retained is not None and (
        retained.event_count, retained.tail_event_id, retained.chain_sha256
    ) != pinned:
        raise ActionAuditSchemaError("retained audit witness changed during review")
    return AuditContinuityWitness(count, tail, chain.hex())
