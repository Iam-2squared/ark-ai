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
from pathlib import Path

from .audit import SQLiteActionAudit, _validate_v1_schema
from .contracts import ActionAuditSchemaError, _canonical_json

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


_WITNESS_TYPE = AuditContinuityWitness
_WITNESS_FIELDS = ("event_count", "tail_event_id", "chain_sha256")
_WITNESS_HOOKS = ("__new__", "__getattribute__", "__getattr__")
_ORIGINAL_WITNESS_INIT = vars(_WITNESS_TYPE)["__init__"]
_ORIGINAL_WITNESS_POST_INIT = vars(_WITNESS_TYPE)["__post_init__"]
_ORIGINAL_WITNESS_FIELDS = tuple(
    vars(_WITNESS_TYPE)[name] for name in _WITNESS_FIELDS
)
_ORIGINAL_WITNESS_HOOKS = tuple(
    vars(_WITNESS_TYPE).get(name) for name in _WITNESS_HOOKS
)


def _require_original_witness_constructor() -> None:
    # An exact frozen instance is insufficient when class-level slots,
    # validators or lookup hooks are replaced with executable descriptors.
    # Check import-original identities BEFORE reading retained audit evidence,
    # opening SQLite, or constructing the result after the read.
    if (
        AuditContinuityWitness is not _WITNESS_TYPE
        or vars(_WITNESS_TYPE).get("__init__") is not _ORIGINAL_WITNESS_INIT
        or vars(_WITNESS_TYPE).get("__post_init__")
        is not _ORIGINAL_WITNESS_POST_INIT
        or any(
            vars(_WITNESS_TYPE).get(name) is not original
            for name, original in zip(
                _WITNESS_FIELDS, _ORIGINAL_WITNESS_FIELDS, strict=True,
            )
        )
        or any(
            vars(_WITNESS_TYPE).get(name) is not original
            for name, original in zip(
                _WITNESS_HOOKS, _ORIGINAL_WITNESS_HOOKS, strict=True,
            )
        )
    ):
        raise ActionAuditSchemaError("audit continuity witness constructor changed")


def _row_payload(row: sqlite3.Row, *, previous_id: int) -> tuple[int, bytes]:
    event_id = row["event_id"]
    occurred = row["occurred_at_ms"]
    if type(event_id) is not int or event_id <= previous_id:
        raise ActionAuditSchemaError("audit event ID must be increasing SQLite INTEGER")
    # The v1 event ledger is append-only: this review starts at genesis,
    # with no legitimate deletion/compaction API. A lost first or middle
    # event must not become a plausible new history merely because later
    # event IDs remain increasing. Independently retained witnesses are
    # still required to catch suffix truncation or rewritten valid rows.
    if event_id != previous_id + 1:
        raise ActionAuditSchemaError("audit event ID gap in append-only history")
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
    # All stored identity fields must agree with the original ToolCall
    # request digest, not merely have individually plausible syntax.
    # The v1 audit schema retains no raw arguments, so this is an
    # internal consistency check, never writer authentication or consent.
    expected_id = "act_" + hashlib.sha256(_canonical_json({
        "arguments_sha256": values["arguments_sha256"],
        "capability": values["capability"],
        "scope": values["scope"],
        "tool": values["tool"],
    })).hexdigest()
    if values["request_id"] != expected_id:
        raise ActionAuditSchemaError(
            "audit continuity request identity is inconsistent"
        )
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
    _require_original_witness_constructor()
    if type(max_events) is not int or not 1 <= max_events <= 10_000:
        raise ValueError("max_events must be an exact integer from 1 to 10000")
    if type(require_monotonic_time) is not bool:
        raise TypeError("require_monotonic_time must be an exact boolean")
    if retained is not None and type(retained) is not AuditContinuityWitness:
        raise TypeError("retained witness must be an exact AuditContinuityWitness")
    pinned = None
    if retained is not None:
        pinned = (retained.event_count, retained.tail_event_id, retained.chain_sha256)

    # Pin the opened SQLite source before any reentrant validation or row
    # processing. Equality of two Path strings is not an identity epoch.
    path_epoch = audit.path
    if not isinstance(path_epoch, Path):
        raise ActionAuditSchemaError("audit continuity requires a Path source")

    def assert_epoch() -> None:
        _require_original_witness_constructor()
        if audit.path is not path_epoch:
            raise ActionAuditSchemaError(
                "audit SQLite source changed during continuity review"
            )
        if retained is not None and (
            type(retained.event_count) is not int
            or type(retained.tail_event_id) is not int
            or type(retained.chain_sha256) is not str
            or retained.event_count is not pinned[0]
            or retained.tail_event_id is not pinned[1]
            or retained.chain_sha256 is not pinned[2]
            or (
                retained.event_count, retained.tail_event_id,
                retained.chain_sha256,
            ) != pinned
        ):
            raise ActionAuditSchemaError("retained audit witness changed during review")

    # A short read transaction pins all event rows to the same SQLite snapshot.
    # Do not issue PRAGMA journal_mode on ordinary read-only diagnostics.
    try:
        # The reviewer must never create a new empty database when the
        # configured audit file is missing, even on a stale audit object.
        # Path resolution, URI building and SQLite handle acquisition are
        # separate reentrant boundaries. Check the original Path and retained
        # witness after EACH one, before a later callback can restore drift.
        resolved = path_epoch.resolve()
        assert_epoch()
        uri = resolved.as_uri() + "?mode=ro"
        assert_epoch()
        with closing(sqlite3.connect(uri, uri=True)) as conn:
            assert_epoch()
            conn.row_factory = sqlite3.Row
            conn.execute("PRAGMA busy_timeout=5000")
            assert_epoch()
            conn.execute("BEGIN")
            assert_epoch()
            # An audit object may outlive an on-disk schema replacement.
            # Validate the exact v1 structure inside the same read snapshot.
            version = conn.execute("PRAGMA user_version").fetchone()[0]
            if type(version) is not int or version != 1:
                raise ActionAuditSchemaError("audit review requires exact schema version 1")
            _validate_v1_schema(conn)
            assert_epoch()
            rows = conn.execute(
                """SELECT event_id,request_id,tool,capability,scope,arguments_sha256,
                          outcome,occurred_at_ms
                FROM action_events ORDER BY event_id LIMIT ?""",
                (max_events + 1,),
            ).fetchall()
            assert_epoch()
            # Capture AUTOINCREMENT's local high-water inside this same
            # read snapshot. A missing terminal event leaves no ID gap in
            # the surviving rows but still advances sqlite_sequence.
            sequence_row = conn.execute(
                "SELECT seq FROM sqlite_sequence WHERE name='action_events'"
            ).fetchone()
            assert_epoch()
            conn.rollback()
    except sqlite3.DatabaseError as exc:
        raise ActionAuditSchemaError("cannot read audit snapshot") from exc
    assert_epoch()
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
        assert_epoch()
        at_ms = row["occurred_at_ms"]
        if require_monotonic_time and at_ms < previous_at:
            raise ActionAuditSchemaError("audit event clock regressed")
        previous_at = at_ms
        chain = hashlib.sha256(chain + b"\n" + payload).digest()
        assert_epoch()
        count += 1
        if pinned is not None and count == pinned[0]:
            if (tail, chain.hex()) != pinned[1:]:
                raise ActionAuditSchemaError("retained audit prefix differs")
    if pinned is not None and count < pinned[0]:
        raise ActionAuditSchemaError("audit history is shorter than retained witness")
    # No audit compaction/delete exists in v1. This detects local suffix
    # truncation even without a separate retained prefix; it does NOT
    # authenticate a writer who can also rewrite sqlite_sequence.
    if (
        (count == 0 and sequence_row is not None)
        or (count > 0 and (
            sequence_row is None or type(sequence_row[0]) is not int
            or sequence_row[0] != tail
        ))
    ):
        raise ActionAuditSchemaError("audit append-only high-water mismatch")
    assert_epoch()
    digest = chain.hex()
    _require_original_witness_constructor()
    witness = _WITNESS_TYPE(count, tail, digest)
    # Even a frozen dataclass may be reflectively edited inside a patched
    # constructor; neither its source nor returned witness may drift while
    # the final read-only diagnostic is being constructed.
    assert_epoch()
    if (
        type(witness) is not AuditContinuityWitness
        or type(witness.event_count) is not int
        or witness.event_count != count
        or type(witness.tail_event_id) is not int
        or witness.tail_event_id != tail
        or type(witness.chain_sha256) is not str
        or witness.chain_sha256 is not digest
    ):
        raise ActionAuditSchemaError(
            "returned audit continuity witness changed during construction"
        )
    return witness
