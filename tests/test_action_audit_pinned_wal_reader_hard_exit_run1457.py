"""Run1457: ActionAudit native COMMIT survives with a pinned WAL reader.

The local audit row is content-minimized evidence only, not proof of an
external effect, issuer authentication, consent, or permission to retry.
"""

from __future__ import annotations

import multiprocessing
import os
import sqlite3
from contextlib import closing
from pathlib import Path

import pytest

from ark.agency.audit import SQLiteActionAudit
from ark.agency.contracts import ToolCall

_PRIVATE = "raw-private-action-audit-arguments-run1457"
_OUTCOME = "synthetic_before_mock"


def _call(number: int) -> ToolCall:
    return ToolCall(
        "fixture.audit",
        "mock.write",
        "synthetic:private",
        {"private_marker": _PRIVATE, "number": number},
    )


def _snapshot(connection: sqlite3.Connection):
    return connection.execute(
        "SELECT event_id,request_id,tool,capability,scope,arguments_sha256,"
        "outcome,occurred_at_ms FROM action_events ORDER BY event_id",
    ).fetchall()


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


def test_action_audit_commit_survives_hard_exit_with_pinned_wal_reader(
    tmp_path: Path,
) -> None:
    path = tmp_path / "action-audit-pinned-wal-reader.sqlite3"
    audit = SQLiteActionAudit(path, clock_ms=lambda: 200)
    first = audit.append(_call(1), outcome=_OUTCOME)

    keeper = sqlite3.connect(path, timeout=10, isolation_level=None)
    keeper_open = True
    process = multiprocessing.get_context("spawn").Process(
        target=_hard_exit_after_native_audit_commit,
        args=(str(path),),
    )
    try:
        keeper.execute("PRAGMA query_only=ON")
        keeper.execute("BEGIN")
        before = _snapshot(keeper)
        assert before == [
            (
                1,
                first.request_id,
                first.tool,
                first.capability,
                first.scope,
                first.arguments_sha256,
                first.outcome,
                first.occurred_at_ms,
            ),
        ]

        process.start()
        process.join(timeout=35)
        if process.is_alive():
            process.terminate()
            process.join(timeout=5)
            pytest.fail("ActionAudit native-COMMIT hard-exit fixture did not terminate")
        assert process.exitcode == 78

        # The pinned reader remains on event 1 after event 2 has committed and
        # the child process has exited without closing its audit connection.
        assert _snapshot(keeper) == before
        with closing(sqlite3.connect(path, timeout=0.2)) as checkpoint:
            blocked = checkpoint.execute("PRAGMA wal_checkpoint(TRUNCATE)").fetchone()
        assert blocked is not None
        assert blocked[0] == 1 or blocked[1] != blocked[2]

        keeper.rollback()
        keeper.close()
        keeper_open = False

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

        with closing(sqlite3.connect(path, timeout=10)) as connection:
            assert connection.execute("PRAGMA quick_check").fetchone() == ("ok",)
            assert connection.execute("PRAGMA user_version").fetchone() == (1,)
            rows = _snapshot(connection)
            assert [row[0] for row in rows] == [1, 2]
            assert [row[1] for row in rows] == [_call(1).request_id, _call(2).request_id]
            assert all(
                row[5] == _call(index).arguments_sha256
                for index, row in enumerate(rows, 1)
            )
            assert [row[6:] for row in rows] == [
                (_OUTCOME, 200),
                (_OUTCOME, 201),
            ]
            checkpoint = connection.execute("PRAGMA wal_checkpoint(TRUNCATE)").fetchone()
            assert checkpoint is not None
            assert checkpoint[0] == 0
            assert checkpoint[1] == checkpoint[2]

        persisted = b"".join(
            item.read_bytes() for item in tmp_path.iterdir() if item.is_file()
        )
        assert _PRIVATE.encode("utf-8") not in persisted
    finally:
        if process.is_alive():
            process.terminate()
            process.join(timeout=5)
        if keeper_open:
            if keeper.in_transaction:
                keeper.rollback()
            keeper.close()
