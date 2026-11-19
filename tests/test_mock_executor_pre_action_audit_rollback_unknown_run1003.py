"""Run1003: a pre-action audit COMMIT rollback still blocks mock WRITE."""

from __future__ import annotations

import sqlite3

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


class _CommitFailsBeforeExecution:
    """Fail before SQLite receives the context-manager COMMIT."""

    def __init__(self, connection):
        self._connection = connection
        self._pre_action_inserted = False
        self._failed = False

    def __setattr__(self, name, value):
        if name in {"_connection", "_pre_action_inserted", "_failed"}:
            object.__setattr__(self, name, value)
        else:
            setattr(self._connection, name, value)

    def __enter__(self):
        self._connection.__enter__()
        return self

    def __exit__(self, *args):
        if args[0] is None and self._pre_action_inserted and not self._failed:
            self._failed = True
            # Do not call the underlying context manager. The outer
            # contextlib.closing closes the connection and SQLite rolls back.
            raise sqlite3.OperationalError(
                "synthetic pre-action audit COMMIT failed before execution"
            )
        return self._connection.__exit__(*args)

    def execute(self, statement, *args):
        cursor = self._connection.execute(statement, *args)
        if (
            type(statement) is str
            and statement.lstrip().startswith("INSERT INTO action_events")
        ):
            parameters = args[0] if args else ()
            if (
                type(parameters) is tuple
                and len(parameters) >= 7
                and parameters[5] == "mock_pre_action"
            ):
                self._pre_action_inserted = True
        return cursor

    def close(self):
        self._connection.close()

    def __getattr__(self, name):
        return getattr(self._connection, name)


def _stack(tmp_path):
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
    audit_path = tmp_path / "action-audit.sqlite3"
    occurrence_path = tmp_path / "occurrences.sqlite3"
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
    return (
        backend, registry, audit, occurrences, executor,
        call, grant, audit_path, occurrence_path,
    )


def test_rollback_side_pre_action_audit_unknown_blocks_backend_and_restart_replay(
    tmp_path, monkeypatch,
):
    (
        backend, registry, audit, occurrences, executor,
        call, grant, audit_path, occurrence_path,
    ) = _stack(tmp_path)
    token = OneShotAuthorization(
        "synthetic-audit-rollback-unknown",
        call.request_id,
        500,
    )
    occurrence_id = "occ_" + "e" * 64

    original_connect = sqlite3.connect
    audit_uri = audit_path.resolve().as_uri() + "?mode=rw"

    def connect(*args, **kwargs):
        database = args[0] if args else kwargs.get("database")
        connection = original_connect(*args, **kwargs)
        if type(database) is str and database == audit_uri:
            return _CommitFailsBeforeExecution(connection)
        return connection

    monkeypatch.setattr(sqlite3, "connect", connect)

    with pytest.raises(
        DisconnectedMockExecutionRejected,
        match="pre-action audit failed; mock backend was not called",
    ):
        executor.execute(
            call,
            (grant,),
            now_ms=100,
            one_shot=token,
            occurrence_id=occurrence_id,
        )

    # The occurrence reservation committed first, but the audit row did not.
    # The executor still fails closed: no mock WRITE and no inferred rollback
    # authorization are returned to the caller.
    assert backend.calls == 0
    assert occurrences.count_synthetic() == 1

    reopened_audit = SQLiteActionAudit(audit_path, clock_ms=lambda: 101)
    reopened_occurrences = SyntheticOccurrenceStore(occurrence_path)
    assert reopened_audit.events() == []

    restarted = DisconnectedMockExecutor(
        registry,
        PermissionGate(),
        reopened_audit,
        reopened_occurrences,
    )
    with pytest.raises(
        DisconnectedMockExecutionRejected,
        match="durable synthetic occurrence reservation failed",
    ):
        restarted.execute(
            call,
            (grant,),
            now_ms=101,
            one_shot=token,
            occurrence_id=occurrence_id,
        )

    assert backend.calls == 0
    assert reopened_occurrences.count_synthetic() == 1
    assert reopened_audit.events() == []
