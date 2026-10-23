"""SQLite action audit storing argument digests, never raw arguments."""

from __future__ import annotations

import sqlite3
import time
from collections.abc import Callable
from contextlib import closing
from pathlib import Path

from .contracts import ActionAuditEvent, ActionAuditSchemaError, ToolCall

SCHEMA_VERSION = 1
_SQLITE_INT_MAX = 2**63 - 1

_AUDIT_SCHEMA_V1_SQL = """CREATE TABLE action_events(
                        event_id INTEGER PRIMARY KEY AUTOINCREMENT,
                        request_id TEXT NOT NULL,
                        tool TEXT NOT NULL,
                        capability TEXT NOT NULL,
                        scope TEXT NOT NULL,
                        arguments_sha256 TEXT NOT NULL,
                        outcome TEXT NOT NULL,
                        occurred_at_ms INTEGER NOT NULL
                    );
                    CREATE INDEX idx_action_request ON action_events(request_id,event_id);
                    PRAGMA user_version=1;"""


def _normalized_ddl(sql: str | None) -> str | None:
    """Ignore unquoted formatting only; quoted SQL and CHECK values stay exact."""
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
        raise ActionAuditSchemaError("unterminated SQLite audit schema quotation")
    return "".join(output)


def _schema_objects(conn: sqlite3.Connection) -> tuple[tuple[object, ...], ...]:
    rows = conn.execute(
        "SELECT type,name,tbl_name,sql FROM sqlite_master ORDER BY type,name"
    ).fetchall()
    return tuple((row[0], row[1], row[2], _normalized_ddl(row[3])) for row in rows)


def _validate_v1_schema(conn: sqlite3.Connection) -> None:
    """Startup-only v1 audit DDL and quick_check gate; never auto-repair."""
    try:
        quick = conn.execute("PRAGMA quick_check").fetchall()
        if len(quick) != 1 or tuple(quick[0]) != ("ok",):
            raise ActionAuditSchemaError("action audit SQLite quick_check failed")
        with sqlite3.connect(":memory:") as expected:
            expected.executescript(_AUDIT_SCHEMA_V1_SQL)
            if _schema_objects(conn) != _schema_objects(expected):
                raise ActionAuditSchemaError(
                    "action audit v1 schema differs from original DDL"
                )
    except sqlite3.DatabaseError as exc:
        raise ActionAuditSchemaError("action audit schema cannot be verified") from exc



class SQLiteActionAudit:
    def __init__(self, path: str | Path, *, clock_ms: Callable[[], int] | None = None) -> None:
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._clock_ms = clock_ms or (lambda: time.time_ns() // 1_000_000)
        self._initialize()

    def append(self, call: ToolCall, *, outcome: str) -> ActionAuditEvent:
        if type(call) is not ToolCall:
            raise TypeError("audit call must be an exact ToolCall")
        if type(outcome) is not str or not outcome.strip():
            raise ValueError("outcome must be a non-empty exact string")
        # Freeze the action identity before a reentrant clock callback. Frozen
        # dataclasses can still be modified by reflection; never mix fields
        # from before/after callback in a persisted audit event.
        try:
            checked = ToolCall(call.tool, call.capability, call.scope, call.arguments)
            identity = (
                checked.request_id, checked.tool, checked.capability,
                checked.scope, checked.arguments_sha256,
            )
            if identity != (
                call.request_id, call.tool, call.capability, call.scope,
                call.arguments_sha256,
            ):
                raise ActionAuditSchemaError("audit call identity is inconsistent")
        except (TypeError, ValueError) as exc:
            raise ActionAuditSchemaError("audit call identity is invalid") from exc
        original_arguments = call.arguments
        with self._connect() as conn:
            # Commit an event with a clock sampled only after acquiring the
            # writer slot; no external backend dispatch is performed here.
            conn.execute("BEGIN IMMEDIATE")
            now = self._now()
            try:
                current = (
                    call.request_id, call.tool, call.capability, call.scope,
                    call.arguments_sha256,
                )
            except (TypeError, ValueError, AttributeError) as exc:
                raise ActionAuditSchemaError(
                    "audit call identity became invalid during clock"
                ) from exc
            if call.arguments is not original_arguments or current != identity:
                raise ActionAuditSchemaError("audit call changed during clock")
            cursor = conn.execute(
                """INSERT INTO action_events(
                    request_id,tool,capability,scope,arguments_sha256,outcome,occurred_at_ms
                ) VALUES(?,?,?,?,?,?,?)""",
                (
                    *identity,
                    outcome,
                    now,
                ),
            )
            event_id = int(cursor.lastrowid)
        return ActionAuditEvent(event_id, *identity, outcome, now)

    def events(self, *, after_event_id: int = 0, limit: int = 100) -> list[ActionAuditEvent]:
        if (
            type(after_event_id) is not int
            or not 0 <= after_event_id <= _SQLITE_INT_MAX
        ):
            raise ValueError("after_event_id must fit a non-negative SQLite INTEGER")
        if type(limit) is not int or not 1 <= limit <= 1000:
            raise ValueError("limit must be an integer from 1 to 1000")
        # The audit object may outlive the SQLite file. Never create an empty
        # replacement database while reading evidence from a stale path.
        with closing(self._connect_readonly()) as conn:
            rows = conn.execute(
                """SELECT * FROM action_events WHERE event_id>?
                ORDER BY event_id LIMIT ?""",
                (after_event_id, limit),
            ).fetchall()
        # Read persisted rows without SQLite's permissive Python coercions.
        # A digest is only a shape check here; it does not attest the issuer
        # or bind back to plaintext arguments that are deliberately not stored.
        result: list[ActionAuditEvent] = []
        previous_id = after_event_id
        for row in rows:
            event_id = row["event_id"]
            occurred = row["occurred_at_ms"]
            if type(event_id) is not int or event_id <= previous_id:
                raise ActionAuditSchemaError("audit event_id must increase as INTEGER")
            previous_id = event_id
            if type(occurred) is not int or occurred < 0:
                raise ActionAuditSchemaError("audit clock must be a non-negative INTEGER")
            fields = ("request_id", "tool", "capability", "scope", "arguments_sha256", "outcome")
            values = [row[column] for column in fields]
            if any(type(value) is not str or not value.strip() for value in values):
                raise ActionAuditSchemaError("audit identity fields must be non-empty TEXT")
            request_id, tool, capability, scope, arguments_sha256, outcome = values
            if (
                len(request_id) != 68 or not request_id.startswith("act_")
                or any(char not in "0123456789abcdef" for char in request_id[4:])
                or len(arguments_sha256) != 64
                or any(char not in "0123456789abcdef" for char in arguments_sha256)
            ):
                raise ActionAuditSchemaError("audit stored digest identity is invalid")
            result.append(ActionAuditEvent(
                event_id, request_id, tool, capability, scope, arguments_sha256, outcome, occurred
            ))
        return result

    def _initialize(self) -> None:
        with self._connect() as conn:
            # Bootstrap must be atomic: executescript() implicitly commits and
            # could leave a partially initialized audit if verification fails.
            conn.execute("BEGIN IMMEDIATE")
            version = int(conn.execute("PRAGMA user_version").fetchone()[0])
            if version < 0:
                raise ActionAuditSchemaError(
                    f"unsupported negative action audit schema version {version}"
                )
            if version > SCHEMA_VERSION:
                raise ActionAuditSchemaError(
                    f"action audit schema {version} is newer than supported {SCHEMA_VERSION}"
                )
            if version == 0:
                # Never treat another or a partially initialized database as
                # an empty audit. There is no implicit repair or migration.
                existing = conn.execute(
                    "SELECT name FROM sqlite_master WHERE name NOT LIKE 'sqlite_%' LIMIT 1"
                ).fetchone()
                if existing is not None:
                    raise ActionAuditSchemaError("unversioned action audit database is not empty")
                for statement in _AUDIT_SCHEMA_V1_SQL.split(";"):
                    if statement.strip():
                        conn.execute(statement)
            _validate_v1_schema(conn)

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.path)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA journal_mode=WAL")
        conn.execute("PRAGMA busy_timeout=5000")
        return conn

    def _connect_readonly(self) -> sqlite3.Connection:
        try:
            conn = sqlite3.connect(self.path.resolve().as_uri() + "?mode=ro", uri=True)
        except sqlite3.DatabaseError as exc:
            raise ActionAuditSchemaError("action audit read-only file is unavailable") from exc
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA busy_timeout=5000")
        return conn

    def _now(self) -> int:
        value = self._clock_ms()
        if type(value) is not int or not 0 <= value <= _SQLITE_INT_MAX:
            raise ValueError(
                "clock_ms must return a non-negative integer within SQLite INTEGER range"
            )
        return value
