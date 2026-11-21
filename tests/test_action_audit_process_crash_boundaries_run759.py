"""OS-process abrupt exit across local action-audit COMMIT boundaries.

Audit evidence is content-minimized and locally durable; it is not execution,
issuer authentication, consent, cross-store atomicity or a replay permission.
"""

from __future__ import annotations

import os
import sqlite3
from multiprocessing import get_context

import pytest

from ark.agency.audit import SQLiteActionAudit
from ark.agency.contracts import ToolCall


def _call(number: int) -> ToolCall:
    return ToolCall(
        "fixture.audit", "mock.write", "synthetic:private",
        {"private_marker": "never-in-audit-sqlite", "number": number},
    )


def _exit_during_audit(path: str, stage: str) -> None:
    if stage == "committed_without_reply":
        audit = SQLiteActionAudit(path, clock_ms=lambda: 201)
        audit.append(_call(2), outcome="synthetic_before_mock")
        os._exit(0)  # Return value is never received by the parent.

    connection = sqlite3.connect(path, timeout=30, isolation_level=None)
    connection.execute("PRAGMA journal_mode=WAL")
    connection.execute("BEGIN IMMEDIATE")
    if stage == "delete_earlier_row":
        connection.execute("DELETE FROM action_events WHERE event_id=1")
    elif stage == "corrupt_earlier_outcome":
        connection.execute(
            "UPDATE action_events SET outcome=? WHERE event_id=1",
            ("uncommitted different outcome",),
        )
    elif stage == "insert_uncommitted_event":
        old = connection.execute(
            "SELECT request_id,tool,capability,scope,arguments_sha256,outcome "
            "FROM action_events WHERE event_id=1"
        ).fetchone()
        connection.execute(
            "INSERT INTO action_events(request_id,tool,capability,scope,"
            "arguments_sha256,outcome,occurred_at_ms) VALUES(?,?,?,?,?,?,?)",
            (*old, 201),
        )
    else:
        raise AssertionError("unsupported local audit crash fixture")
    os._exit(0)  # No COMMIT, exception unwinding or audit response.


@pytest.mark.parametrize(
    "stage", (
        "delete_earlier_row", "corrupt_earlier_outcome",
        "insert_uncommitted_event",
    ),
)
def test_abandoned_audit_wal_transaction_does_not_change_committed_prefix(
    tmp_path, stage,
):
    path = tmp_path / "action-audit-abrupt.sqlite3"
    audit = SQLiteActionAudit(path, clock_ms=lambda: 200)
    original = audit.append(_call(1), outcome="synthetic_before_mock")
    baseline = tuple(audit.events())
    assert original.event_id == 1
    child = get_context("spawn").Process(
        target=_exit_during_audit, args=(str(path), stage),
    )
    child.start()
    child.join(timeout=35)
    if child.is_alive():
        child.terminate()
        child.join(timeout=5)
    assert child.exitcode == 0

    cold = SQLiteActionAudit(path, clock_ms=lambda: 202)
    assert tuple(cold.events()) == baseline
    second = cold.append(_call(2), outcome="synthetic_before_mock")
    assert second.event_id == 2
    assert [item.event_id for item in cold.events()] == [1, 2]
    assert b"never-in-audit-sqlite" not in path.read_bytes()


def test_postcommit_audit_worker_exit_requires_readback_not_auto_replay(tmp_path):
    path = tmp_path / "action-audit-lost-result.sqlite3"
    audit = SQLiteActionAudit(path, clock_ms=lambda: 200)
    first = audit.append(_call(1), outcome="synthetic_before_mock")
    child = get_context("spawn").Process(
        target=_exit_during_audit,
        args=(str(path), "committed_without_reply"),
    )
    child.start()
    child.join(timeout=35)
    if child.is_alive():
        child.terminate()
        child.join(timeout=5)
    assert child.exitcode == 0

    cold = SQLiteActionAudit(path, clock_ms=lambda: 202)
    events = cold.events()
    assert [item.event_id for item in events] == [1, 2]
    assert events[0] == first
    assert events[1].request_id == _call(2).request_id
    assert events[1].occurred_at_ms == 201
    assert events[1].outcome == "synthetic_before_mock"
    # A local audit row cannot say if a tool effect took place. Do NOT append
    # another event or retry an ambiguous external WRITE from this observation.
    assert b"never-in-audit-sqlite" not in path.read_bytes()
