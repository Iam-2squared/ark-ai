"""SQLite action audit storing argument digests, never raw arguments."""

from __future__ import annotations

import sqlite3
import time
from collections.abc import Callable
from pathlib import Path

from .contracts import ActionAuditEvent, ActionAuditSchemaError, ToolCall

SCHEMA_VERSION = 1


class SQLiteActionAudit:
    def __init__(self, path: str | Path, *, clock_ms: Callable[[], int] | None = None) -> None:
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._clock_ms = clock_ms or (lambda: time.time_ns() // 1_000_000)
        self._initialize()

    def append(self, call: ToolCall, *, outcome: str) -> ActionAuditEvent:
        if not isinstance(outcome, str) or not outcome.strip():
            raise ValueError("outcome must be a non-empty string")
        now = self._now()
        with self._connect() as conn:
            cursor = conn.execute(
                """INSERT INTO action_events(
                    request_id,tool,capability,scope,arguments_sha256,outcome,occurred_at_ms
                ) VALUES(?,?,?,?,?,?,?)""",
                (
                    call.request_id,
                    call.tool,
                    call.capability,
                    call.scope,
                    call.arguments_sha256,
                    outcome,
                    now,
                ),
            )
            event_id = int(cursor.lastrowid)
        return ActionAuditEvent(
            event_id,
            call.request_id,
            call.tool,
            call.capability,
            call.scope,
            call.arguments_sha256,
            outcome,
            now,
        )

    def events(self, *, after_event_id: int = 0, limit: int = 100) -> list[ActionAuditEvent]:
        if type(after_event_id) is not int or after_event_id < 0:
            raise ValueError("after_event_id must be a non-negative integer")
        if type(limit) is not int or not 1 <= limit <= 1000:
            raise ValueError("limit must be an integer from 1 to 1000")
        with self._connect() as conn:
            rows = conn.execute(
                """SELECT * FROM action_events WHERE event_id>?
                ORDER BY event_id LIMIT ?""",
                (after_event_id, limit),
            ).fetchall()
        return [
            ActionAuditEvent(
                int(row["event_id"]),
                row["request_id"],
                row["tool"],
                row["capability"],
                row["scope"],
                row["arguments_sha256"],
                row["outcome"],
                int(row["occurred_at_ms"]),
            )
            for row in rows
        ]

    def _initialize(self) -> None:
        with self._connect() as conn:
            version = int(conn.execute("PRAGMA user_version").fetchone()[0])
            if version > SCHEMA_VERSION:
                raise ActionAuditSchemaError(
                    f"action audit schema {version} is newer than supported {SCHEMA_VERSION}"
                )
            if version == 0:
                conn.executescript(
                    """CREATE TABLE action_events(
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
