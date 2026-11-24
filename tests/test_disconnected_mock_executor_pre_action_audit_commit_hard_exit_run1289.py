"""Run1289: process exit after pre-action audit COMMIT cannot dispatch or replay.

Synthetic local SQLite only. The child exits after the native ActionAudit
transaction commits but before append() returns to the executor. Recovery must
retain the pre-action event and occurrence reservation, show no completion
event, and deny the same token before a fresh gate or mock call. This is not
power-loss, trusted-time, or external-effect evidence.
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


def test_pre_action_audit_commit_hard_exit_never_dispatches_or_replays(
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
AUDIT_RW_URI = AUDIT_PATH.resolve().as_uri() + "?mode=rw"

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
token = OneShotAuthorization("run1289-token", call.request_id, 500)

native_connect = sqlite3.connect
armed = False


class CommitExit:
    def __init__(self, connection):
        self.connection = connection

    def __enter__(self):
        self.connection.__enter__()
        return self

    def __exit__(self, exc_type, exc, traceback):
        result = self.connection.__exit__(exc_type, exc, traceback)
        if armed and exc_type is None:
            os._exit(48)
        return result

    def close(self):
        self.connection.close()

    def __getattr__(self, name):
        return getattr(self.connection, name)


def controlled_connect(database, *args, **kwargs):
    connection = native_connect(database, *args, **kwargs)
    if armed and database == AUDIT_RW_URI:
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
raise AssertionError("child returned instead of exiting after ActionAudit COMMIT")
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
    assert result.returncode == 48, result.stdout + result.stderr
    assert gate_marker.exists()
    assert audit_marker.exists()
    assert not backend_marker.exists()

    # Cold recovery retains both commits, but no completion event.
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
    token = OneShotAuthorization("run1289-token", call.request_id, 500)

    assert occurrences.count_synthetic() == 1
    assert [event.outcome for event in audit.events()] == ["mock_pre_action"]

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
    assert [event.outcome for event in audit.events()] == ["mock_pre_action"]
