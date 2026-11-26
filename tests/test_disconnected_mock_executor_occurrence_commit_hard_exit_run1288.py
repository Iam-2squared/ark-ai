"""Run1288: process exit after occurrence COMMIT cannot authorize a replay.

Synthetic local SQLite only. The child exits after native reservation COMMIT
returns but before the reservation receipt, actual gate consumption, pre-action
audit, or mock backend call. Cold recovery must retain the reservation and deny
the same one-shot token. This is not power-loss or external-effect evidence.
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pytest

from ark.agency import (
    CapabilityGrant,
    Effect,
    OneShotAuthorization,
    PermissionGate,
    SQLiteActionAudit,
    ToolCall,
    ToolRegistration,
    ToolRegistry,
)
from ark.agency.disconnected_mock_executor import (
    DisconnectedMockExecutionRejected,
    DisconnectedMockExecutor,
    MockToolBackend,
)
from ark.agency.durable_occurrence_review import SyntheticOccurrenceStore


def test_occurrence_commit_hard_exit_before_audit_or_mock_prevents_replay(
    tmp_path: Path,
) -> None:
    audit_path = tmp_path / "action-audit.sqlite3"
    occurrence_path = tmp_path / "occurrences.sqlite3"
    gate_marker = tmp_path / "actual-gate-called"
    audit_marker = tmp_path / "audit-append-called"
    backend_marker = tmp_path / "mock-backend-called"

    script = r"""
import os
import sqlite3
import sys
from pathlib import Path

AUDIT_PATH = Path(__AUDIT_PATH__)
OCCURRENCE_PATH = Path(__OCCURRENCE_PATH__)
GATE_MARKER = Path(__GATE_MARKER__)
AUDIT_MARKER = Path(__AUDIT_MARKER__)
BACKEND_MARKER = Path(__BACKEND_MARKER__)
OCCURRENCE_RW_URI = OCCURRENCE_PATH.resolve().as_uri() + "?mode=rw"

from ark.agency import (
    CapabilityGrant,
    Effect,
    OneShotAuthorization,
    PermissionGate,
    SQLiteActionAudit,
    ToolCall,
    ToolRegistration,
    ToolRegistry,
)
from ark.agency.disconnected_mock_executor import (
    DisconnectedMockExecutor,
    MockToolBackend,
)
from ark.agency.durable_occurrence_review import SyntheticOccurrenceStore

backend = MockToolBackend()
registry = ToolRegistry((
    ToolRegistration(
        "fixture.mock", "fixture.mock", Effect.WRITE,
        "ark.mock.fixture.v1", backend,
    ),
))
gate = PermissionGate()
audit = SQLiteActionAudit(AUDIT_PATH, clock_ms=lambda: 100)
occurrences = SyntheticOccurrenceStore(OCCURRENCE_PATH)
executor = DisconnectedMockExecutor(registry, gate, audit, occurrences)
call = ToolCall(
    "fixture.mock", "fixture.mock", "synthetic:private",
    {"value": "fixture-only"},
)
grant = CapabilityGrant("fixture.mock", "synthetic:private")
token = OneShotAuthorization("run1288-token", call.request_id, 500)

native_connect = sqlite3.connect
armed = False


class CommitExit:
    def __init__(self, connection):
        self.connection = connection

    def commit(self):
        self.connection.commit()
        if armed:
            os._exit(47)

    def close(self):
        self.connection.close()

    def __getattr__(self, name):
        return getattr(self.connection, name)


def controlled_connect(database, *args, **kwargs):
    connection = native_connect(database, *args, **kwargs)
    if armed and database == OCCURRENCE_RW_URI:
        return CommitExit(connection)
    return connection


sqlite3.connect = controlled_connect
gate_code = PermissionGate.authorize_registered.__code__
audit_code = SQLiteActionAudit.append.__code__
backend_code = MockToolBackend.execute.__code__


def profile(frame, event, _argument):
    if event != "call":
        return
    if frame.f_code is gate_code and frame.f_locals.get("self") is gate:
        GATE_MARKER.write_text("called", encoding="utf-8")
    elif frame.f_code is audit_code:
        AUDIT_MARKER.write_text("called", encoding="utf-8")
    elif frame.f_code is backend_code:
        BACKEND_MARKER.write_text("called", encoding="utf-8")


sys.setprofile(profile)
armed = True
executor.execute(
    call,
    (grant,),
    now_ms=100,
    one_shot=token,
    occurrence_id="occ_" + "a" * 64,
)
raise AssertionError("child returned instead of exiting after occurrence COMMIT")
"""
    script = (
        script
        .replace("__AUDIT_PATH__", repr(str(audit_path)))
        .replace("__OCCURRENCE_PATH__", repr(str(occurrence_path)))
        .replace("__GATE_MARKER__", repr(str(gate_marker)))
        .replace("__AUDIT_MARKER__", repr(str(audit_marker)))
        .replace("__BACKEND_MARKER__", repr(str(backend_marker)))
    )
    result = subprocess.run(
        [sys.executable, "-c", script],
        capture_output=True,
        text=True,
        timeout=90,
        check=False,
    )
    assert result.returncode == 47, result.stdout + result.stderr
    assert not gate_marker.exists()
    assert not audit_marker.exists()
    assert not backend_marker.exists()

    # Cold recovery sees the committed reservation but no pre-action audit.
    backend = MockToolBackend()
    registry = ToolRegistry((
        ToolRegistration(
            "fixture.mock", "fixture.mock", Effect.WRITE,
            "ark.mock.fixture.v1", backend,
        ),
    ))
    gate = PermissionGate()
    audit = SQLiteActionAudit(audit_path, clock_ms=lambda: 101)
    occurrences = SyntheticOccurrenceStore(occurrence_path)
    executor = DisconnectedMockExecutor(registry, gate, audit, occurrences)
    call = ToolCall(
        "fixture.mock", "fixture.mock", "synthetic:private",
        {"value": "fixture-only"},
    )
    grant = CapabilityGrant("fixture.mock", "synthetic:private")
    token = OneShotAuthorization("run1288-token", call.request_id, 500)

    assert occurrences.count_synthetic() == 1
    assert audit.events() == []

    with pytest.raises(
        DisconnectedMockExecutionRejected,
        match="durable synthetic occurrence reservation failed",
    ):
        executor.execute(
            call,
            (grant,),
            now_ms=101,
            one_shot=token,
            occurrence_id="occ_" + "b" * 64,
        )

    assert gate._consumed_tokens == set()
    assert occurrences.count_synthetic() == 1
    assert backend.calls == 0
    assert audit.events() == []
