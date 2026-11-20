"""Run1009: hard process exit after pre-action audit COMMIT remains non-replayable.

The child commits the local pre-action audit row, then exits inside the SQLite
context-manager acknowledgement boundary before append returns to the executor.
The mock backend is therefore not reached in this process. A fresh process must
observe the durable occurrence reservation and deny replay without appending a
second audit event. Both stores contain disposable synthetic local fixtures;
this is not cross-store atomicity, trusted consent/time, or external-effect proof.
"""

from __future__ import annotations

import multiprocessing
import os
import sqlite3
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

_TOKEN_ID = "synthetic-pre-action-crash-token"
_OCCURRENCE_ID = "occ_" + "e" * 64


def _stack(audit_path: Path, occurrence_path: Path):
    backend = MockToolBackend()
    registry = ToolRegistry((
        ToolRegistration(
            "fixture.mock",
            "fixture.mock",
            Effect.WRITE,
            "ark.mock.fixture.v1",
            backend,
        ),
    ))
    gate = PermissionGate()
    audit = SQLiteActionAudit(audit_path, clock_ms=lambda: 100)
    occurrences = SyntheticOccurrenceStore(occurrence_path)
    executor = DisconnectedMockExecutor(registry, gate, audit, occurrences)
    call = ToolCall(
        "fixture.mock",
        "fixture.mock",
        "synthetic:private",
        {"value": "fixture-only"},
    )
    grant = CapabilityGrant("fixture.mock", "synthetic:private")
    return backend, executor, call, grant, audit, occurrences


class _ExitAfterPreActionAuditCommit:
    """Commit one pre-action event, then exit before append returns."""

    def __init__(self, connection: sqlite3.Connection, marker: str):
        self._connection = connection
        self._marker = marker
        self._pre_action_inserted = False

    def execute(self, statement, *args):
        cursor = self._connection.execute(statement, *args)
        parameters = args[0] if args else ()
        if (
            type(statement) is str
            and statement.lstrip().startswith("INSERT INTO action_events")
            and type(parameters) is tuple
            and len(parameters) == 7
            and parameters[5] == "mock_pre_action"
        ):
            self._pre_action_inserted = True
        return cursor

    def __enter__(self):
        self._connection.__enter__()
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        result = self._connection.__exit__(exc_type, exc_value, traceback)
        if exc_type is None and self._pre_action_inserted:
            Path(self._marker).write_text("pre-action-committed", encoding="ascii")
            # The underlying context manager has committed. Terminate before
            # SQLiteActionAudit.append can return to DisconnectedMockExecutor.
            os._exit(0)
        return result

    def close(self):
        return self._connection.close()

    def __getattr__(self, name):
        return getattr(self._connection, name)


def _crash_after_pre_action_audit_commit(
    audit_path: str, occurrence_path: str, marker: str,
) -> None:
    audit = Path(audit_path)
    occurrences = Path(occurrence_path)
    _, executor, call, grant, _, _ = _stack(audit, occurrences)
    token = OneShotAuthorization(_TOKEN_ID, call.request_id, 500)

    original_connect = sqlite3.connect
    audit_uri = audit.resolve().as_uri() + "?mode=rw"

    def connect(*args, **kwargs):
        database = args[0] if args else kwargs.get("database")
        connection = original_connect(*args, **kwargs)
        if type(database) is str and database == audit_uri:
            return _ExitAfterPreActionAuditCommit(connection, marker)
        return connection

    # Only the spawned child is patched, and only the existing audit database
    # is wrapped. Occurrence reservation uses its own unmodified SQLite store.
    sqlite3.connect = connect
    executor.execute(
        call,
        (grant,),
        now_ms=100,
        one_shot=token,
        occurrence_id=_OCCURRENCE_ID,
    )
    # Reaching here means the exact commit/return boundary was not intercepted.
    os._exit(9)


def test_pre_action_audit_commit_process_crash_keeps_occurrence_reserved_and_denies_replay(
    tmp_path: Path,
) -> None:
    audit_path = tmp_path / "audit.sqlite3"
    occurrence_path = tmp_path / "occurrences.sqlite3"
    marker = tmp_path / "pre-action-audit-committed"
    _, _, _, _, audit, occurrences = _stack(audit_path, occurrence_path)

    process = multiprocessing.get_context("spawn").Process(
        target=_crash_after_pre_action_audit_commit,
        args=(str(audit_path), str(occurrence_path), str(marker)),
    )
    process.start()
    process.join(timeout=35)
    if process.is_alive():
        process.terminate()
        process.join(timeout=5)

    assert process.exitcode == 0
    assert marker.read_text(encoding="ascii") == "pre-action-committed"

    # Both local commits survive. The executor was terminated before the
    # pre-action append returned, so source order proves it never reached the
    # sole mock backend call in the child.
    assert occurrences.count_synthetic() == 1
    events = audit.events()
    assert len(events) == 1
    assert events[0].outcome == "mock_pre_action"
    assert events[0].request_id == _stack(
        audit_path, occurrence_path,
    )[2].request_id

    # A fresh process-local gate cannot override the durable occurrence row.
    backend, restarted, call, grant, reopened_audit, reopened_occurrences = _stack(
        audit_path, occurrence_path,
    )
    token = OneShotAuthorization(_TOKEN_ID, call.request_id, 500)
    with pytest.raises(
        DisconnectedMockExecutionRejected,
        match="durable synthetic occurrence reservation failed",
    ):
        restarted.execute(
            call,
            (grant,),
            now_ms=101,
            one_shot=token,
            occurrence_id=_OCCURRENCE_ID,
        )

    assert backend.calls == 0
    assert reopened_occurrences.count_synthetic() == 1
    reopened_events = reopened_audit.events()
    assert len(reopened_events) == 1
    assert reopened_events[0].outcome == "mock_pre_action"
    assert _TOKEN_ID.encode("utf-8") not in occurrence_path.read_bytes()
    assert b"fixture-only" not in audit_path.read_bytes()
