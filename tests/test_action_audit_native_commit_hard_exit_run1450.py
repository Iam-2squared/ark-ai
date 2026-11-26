"""Run1450: ActionAudit append survives exit at native SQLite COMMIT.

The audit row is local content-minimized evidence only. It is not proof of an
external effect, issuer authentication, consent, or permission to retry.
"""

from __future__ import annotations

import multiprocessing
import os
import sqlite3
from pathlib import Path

from ark.agency.audit import SQLiteActionAudit
from ark.agency.contracts import ToolCall

_PRIVATE = "raw-private-action-audit-arguments-run1450"
_OUTCOME = "synthetic_before_mock"


def _call(number: int) -> ToolCall:
    return ToolCall(
        "fixture.audit",
        "mock.write",
        "synthetic:private",
        {"private_marker": _PRIVATE, "number": number},
    )


def _hard_exit_after_native_audit_commit(database: str) -> None:
    audit = SQLiteActionAudit(Path(database), clock_ms=lambda: 201)
    native_connect = audit._connect

    class ExitAfterCommit:
        def __init__(self, connection: sqlite3.Connection) -> None:
            self.connection = connection

        def __enter__(self):
            self.connection.__enter__()
            return self

        def __exit__(self, exc_type, exc, traceback):
            result = self.connection.__exit__(exc_type, exc, traceback)
            if exc_type is None:
                # Native SQLite COMMIT returned. Exit before close or receipt.
                os._exit(78)
            return result

        def close(self) -> None:
            self.connection.close()

        def __getattr__(self, name: str):
            return getattr(self.connection, name)

    audit._connect = lambda **kwargs: ExitAfterCommit(native_connect(**kwargs))
    audit.append(_call(2), outcome=_OUTCOME)
    os._exit(79)


def test_action_audit_row_survives_hard_exit_after_native_commit(
    tmp_path: Path,
) -> None:
    path = tmp_path / "action-audit-native-commit-hard-exit.sqlite3"
    audit = SQLiteActionAudit(path, clock_ms=lambda: 200)
    first = audit.append(_call(1), outcome=_OUTCOME)

    process = multiprocessing.get_context("spawn").Process(
        target=_hard_exit_after_native_audit_commit,
        args=(str(path),),
    )
    process.start()
    process.join(timeout=35)
    if process.is_alive():
        process.terminate()
        process.join(timeout=5)
    assert process.exitcode == 78

    cold = SQLiteActionAudit(path, clock_ms=lambda: 300)
    events = cold.events()
    assert [event.event_id for event in events] == [1, 2]
    assert events[0] == first
    assert events[1].request_id == _call(2).request_id
    assert events[1].tool == "fixture.audit"
    assert events[1].capability == "mock.write"
    assert events[1].scope == "synthetic:private"
    assert events[1].outcome == _OUTCOME
    assert events[1].occurred_at_ms == 201

    with sqlite3.connect(path) as connection:
        assert connection.execute("PRAGMA quick_check").fetchone() == ("ok",)
        assert connection.execute("PRAGMA user_version").fetchone() == (1,)
        rows = connection.execute(
            "SELECT event_id,request_id,tool,capability,scope,"
            "arguments_sha256,outcome,occurred_at_ms "
            "FROM action_events ORDER BY event_id"
        ).fetchall()
    assert [row[0] for row in rows] == [1, 2]
    assert [row[1] for row in rows] == [_call(1).request_id, _call(2).request_id]
    assert all(row[5] == _call(index).arguments_sha256 for index, row in enumerate(rows, 1))
    assert [row[6:] for row in rows] == [
        (_OUTCOME, 200),
        (_OUTCOME, 201),
    ]

    persisted = b"".join(
        item.read_bytes() for item in tmp_path.iterdir() if item.is_file()
    )
    assert _PRIVATE.encode("utf-8") not in persisted
