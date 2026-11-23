"""Run1146: executor quarantines ambiguous pre-action audit COMMIT outcomes."""

from __future__ import annotations

import subprocess
import sys

import pytest


@pytest.mark.parametrize("durable", (False, True))
def test_pre_action_audit_commit_ack_loss_never_calls_or_replays_mock(
    tmp_path, durable: bool,
) -> None:
    audit_path = tmp_path / "action-audit.sqlite3"
    occurrence_path = tmp_path / "occurrences.sqlite3"
    script = r"""
import sqlite3
from pathlib import Path

AUDIT_PATH = Path(__AUDIT_PATH__)
OCCURRENCE_PATH = Path(__OCCURRENCE_PATH__)
AUDIT_RW_URI = AUDIT_PATH.resolve().as_uri() + "?mode=rw"
DURABLE = __DURABLE__
armed = False
native_connect = sqlite3.connect


class CommitBoundary:
    def __init__(self, connection):
        object.__setattr__(self, "connection", connection)

    def __enter__(self):
        self.connection.__enter__()
        return self

    def __exit__(self, exc_type, exc, traceback):
        if exc_type is not None:
            return self.connection.__exit__(exc_type, exc, traceback)
        if DURABLE:
            self.connection.commit()
        else:
            self.connection.rollback()
        raise sqlite3.OperationalError(
            "synthetic pre-action audit COMMIT acknowledgement lost"
        )

    def close(self):
        self.connection.close()

    def __getattr__(self, name):
        return getattr(self.connection, name)

    def __setattr__(self, name, value):
        if name == "connection":
            object.__setattr__(self, name, value)
        else:
            setattr(self.connection, name, value)


def controlled_connect(database, *args, **kwargs):
    connection = native_connect(database, *args, **kwargs)
    if armed and database == AUDIT_RW_URI:
        return CommitBoundary(connection)
    return connection


# The audit and executor modules capture this factory at import. It remains
# stable for the entire subprocess; only the selected audit connection gets
# an acknowledgement-loss wrapper after normal initialization.
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
    DisconnectedMockExecutionRejected,
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
token = OneShotAuthorization("run1146-token", call.request_id, 500)

armed = True
try:
    executor.execute(
        call, (grant,), now_ms=100, one_shot=token,
        occurrence_id="occ_" + "a" * 64,
    )
except DisconnectedMockExecutionRejected as exc:
    assert "pre-action audit failed; mock backend was not called" in str(exc)
else:
    raise AssertionError("ambiguous pre-action audit result returned a receipt")
finally:
    armed = False

assert backend.calls == 0
assert gate._consumed_tokens == {"run1146-token"}

# Restart both local stores after the ambiguous audit acknowledgement. The
# occurrence reservation must remain durable regardless of audit COMMIT fate.
recovered_occurrences = SyntheticOccurrenceStore(OCCURRENCE_PATH)
assert recovered_occurrences.count_synthetic() == 1
recovered_audit = SQLiteActionAudit(AUDIT_PATH, clock_ms=lambda: 101)
expected_outcomes = ["mock_pre_action"] if DURABLE else []
assert [event.outcome for event in recovered_audit.events()] == expected_outcomes

# A fresh process-local gate cannot turn the already-reserved token into a
# retry. Use the same token identity with a different occurrence identifier.
replay_gate = PermissionGate()
replay_executor = DisconnectedMockExecutor(
    registry, replay_gate, recovered_audit, recovered_occurrences,
)
replay_token = OneShotAuthorization("run1146-token", call.request_id, 500)
try:
    replay_executor.execute(
        call, (grant,), now_ms=101, one_shot=replay_token,
        occurrence_id="occ_" + "b" * 64,
    )
except DisconnectedMockExecutionRejected as exc:
    assert "durable synthetic occurrence reservation failed" in str(exc)
else:
    raise AssertionError("restart replay passed a previously reserved token")

assert replay_gate._consumed_tokens == set()
assert recovered_occurrences.count_synthetic() == 1
assert backend.calls == 0
assert [event.outcome for event in recovered_audit.events()] == expected_outcomes
"""
    script = (
        script
        .replace("__AUDIT_PATH__", repr(str(audit_path)))
        .replace("__OCCURRENCE_PATH__", repr(str(occurrence_path)))
        .replace("__DURABLE__", repr(durable))
    )
    result = subprocess.run(
        [sys.executable, "-c", script],
        capture_output=True,
        text=True,
        timeout=90,
        check=False,
    )
    assert result.returncode == 0, result.stdout + result.stderr
