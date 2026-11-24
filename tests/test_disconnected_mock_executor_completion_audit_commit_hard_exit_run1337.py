"""Run1337: completion-audit COMMIT hard exit cannot replay a mock WRITE.

Synthetic local SQLite only. The child commits the completion event and exits
before append() returns a receipt to its caller. Recovery must retain the
pre-action/completion events and the occurrence reservation. Reusing the old
one-shot is denied before a fresh gate or backend call; a distinct new one-shot
may create a distinct mock occurrence. This is not external-effect, power-loss,
or trusted-clock evidence.
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


def test_completion_audit_commit_hard_exit_quarantines_old_occurrence(
    tmp_path: Path,
) -> None:
    audit_path = tmp_path / "action-audit.sqlite3"
    occurrence_path = tmp_path / "occurrences.sqlite3"
    timeline_path = tmp_path / "execution-timeline.txt"

    script = r"""
import os
import sqlite3
import sys
from pathlib import Path

AUDIT_PATH = Path(__AUDIT_PATH__)
OCCURRENCE_PATH = Path(__OCCURRENCE_PATH__)
TIMELINE_PATH = Path(__TIMELINE_PATH__)
AUDIT_RW_URI = AUDIT_PATH.resolve().as_uri() + "?mode=rw"

native_connect = sqlite3.connect
armed = False
audit_commits = 0


class CommitExit:
    def __init__(self, connection):
        self.connection = connection

    def __enter__(self):
        self.connection.__enter__()
        return self

    def __exit__(self, exc_type, exc, traceback):
        global audit_commits
        result = self.connection.__exit__(exc_type, exc, traceback)
        if armed and exc_type is None:
            audit_commits += 1
            # The first successful commit is mock_pre_action. Exit only after
            # the second (mock_completed) native commit has returned.
            if audit_commits == 2:
                os._exit(49)
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


# The audit module captures sqlite3.connect at import time. Install the
# wrapper first, then initialize every component before arming the fault.
sqlite3.connect = controlled_connect

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
token = OneShotAuthorization("run1337-token", call.request_id, 500)

gate_code = PermissionGate.authorize_registered.__code__
audit_code = SQLiteActionAudit.append.__code__
backend_code = MockToolBackend.execute.__code__


def mark(value):
    with TIMELINE_PATH.open("a", encoding="utf-8") as stream:
        stream.write(value + "\n")


def profile(frame, event, _argument):
    if event != "call":
        return
    if frame.f_code is gate_code and frame.f_locals.get("self") is gate:
        mark("gate")
    elif frame.f_code is audit_code:
        mark("audit")
    elif frame.f_code is backend_code:
        mark("backend")


sys.setprofile(profile)
armed = True
executor.execute(
    call,
    (grant,),
    now_ms=100,
    one_shot=token,
    occurrence_id="occ_" + "a" * 64,
)
raise AssertionError("child returned instead of exiting after completion COMMIT")
"""
    script = (
        script
        .replace("__AUDIT_PATH__", repr(str(audit_path)))
        .replace("__OCCURRENCE_PATH__", repr(str(occurrence_path)))
        .replace("__TIMELINE_PATH__", repr(str(timeline_path)))
    )
    result = subprocess.run(
        [sys.executable, "-c", script],
        capture_output=True,
        text=True,
        timeout=90,
        check=False,
    )
    assert result.returncode == 49, result.stdout + result.stderr
    assert timeline_path.read_text(encoding="utf-8").splitlines() == [
        "gate", "audit", "backend", "audit",
    ]

    # Cold recovery observes both committed audit events and the durable
    # occurrence, even though the caller never received its receipt.
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
    old_token = OneShotAuthorization("run1337-token", call.request_id, 500)

    assert occurrences.count_synthetic() == 1
    assert [event.outcome for event in audit.events()] == [
        "mock_pre_action", "mock_completed",
    ]

    with pytest.raises(
        DisconnectedMockExecutionRejected,
        match="durable synthetic occurrence reservation failed",
    ):
        executor.execute(
            call,
            (grant,),
            now_ms=101,
            one_shot=old_token,
            occurrence_id="occ_" + "b" * 64,
        )

    assert gate._consumed_tokens == set()
    assert backend.calls == 0
    assert occurrences.count_synthetic() == 1
    assert [event.outcome for event in audit.events()] == [
        "mock_pre_action", "mock_completed",
    ]

    # The same canonical request remains eligible for a separately authorized
    # occurrence; request_id is not a permanent deduplication key.
    new_token = OneShotAuthorization("run1337-token-new", call.request_id, 500)
    receipt = executor.execute(
        call,
        (grant,),
        now_ms=102,
        one_shot=new_token,
        occurrence_id="occ_" + "c" * 64,
    )

    assert receipt.occurrence_id == "occ_" + "c" * 64
    assert receipt.mock_only is True
    assert receipt.external_effect_proven is False
    assert backend.calls == 1
    assert occurrences.count_synthetic() == 2
    assert [event.outcome for event in audit.events()] == [
        "mock_pre_action", "mock_completed",
        "mock_pre_action", "mock_completed",
    ]
