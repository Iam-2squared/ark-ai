"""Run1345: a returned mock result without completion audit is quarantined.

Synthetic local SQLite only. The child exits at entry to the completion-audit
append, after the exact mock backend method has returned. Recovery must retain
the pre-action event and occurrence reservation but must not invent a
completion event. Reusing the old one-shot is denied before a fresh gate or
backend call. A distinct new one-shot may create a distinct mock occurrence.
This is not external-effect, power-loss, or trusted-clock evidence.
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


def test_mock_backend_return_then_exit_before_completion_audit(
    tmp_path: Path,
) -> None:
    audit_path = tmp_path / "action-audit.sqlite3"
    occurrence_path = tmp_path / "occurrences.sqlite3"
    timeline_path = tmp_path / "execution-timeline.txt"

    script = r"""
import os
import sys
from pathlib import Path

AUDIT_PATH = Path(__AUDIT_PATH__)
OCCURRENCE_PATH = Path(__OCCURRENCE_PATH__)
TIMELINE_PATH = Path(__TIMELINE_PATH__)

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
token = OneShotAuthorization("run1345-token", call.request_id, 500)

gate_code = PermissionGate.authorize_registered.__code__
audit_code = SQLiteActionAudit.append.__code__
backend_code = MockToolBackend.execute.__code__
audit_calls = 0


def mark(value):
    with TIMELINE_PATH.open("a", encoding="utf-8") as stream:
        stream.write(value + "\n")


def profile(frame, event, _argument):
    global audit_calls
    if (
        frame.f_code is gate_code
        and event == "call"
        and frame.f_locals.get("self") is gate
    ):
        mark("gate")
    elif frame.f_code is audit_code and event == "call":
        audit_calls += 1
        if audit_calls == 1:
            mark("pre_action_audit")
        elif audit_calls == 2:
            # The backend has already returned. Exit before the completion
            # append body can create or commit a completion event.
            mark("completion_audit_entry")
            os._exit(50)
    elif frame.f_code is backend_code and event == "return":
        mark("backend_return")


sys.setprofile(profile)
executor.execute(
    call,
    (grant,),
    now_ms=100,
    one_shot=token,
    occurrence_id="occ_" + "a" * 64,
)
raise AssertionError("child returned instead of exiting at completion-audit entry")
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
    assert result.returncode == 50, result.stdout + result.stderr
    assert timeline_path.read_text(encoding="utf-8").splitlines() == [
        "gate", "pre_action_audit", "backend_return", "completion_audit_entry",
    ]

    # Cold recovery sees the committed pre-action event and durable
    # occurrence, but no completion event, even though the backend returned.
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
    old_token = OneShotAuthorization("run1345-token", call.request_id, 500)

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
            one_shot=old_token,
            occurrence_id="occ_" + "b" * 64,
        )

    assert gate._consumed_tokens == set()
    assert backend.calls == 0
    assert occurrences.count_synthetic() == 1
    assert [event.outcome for event in audit.events()] == ["mock_pre_action"]

    # The same canonical request remains eligible for a separately authorized
    # occurrence; request_id is not a permanent deduplication key.
    new_token = OneShotAuthorization("run1345-token-new", call.request_id, 500)
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
        "mock_pre_action", "mock_pre_action", "mock_completed",
    ]
