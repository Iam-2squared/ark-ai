"""Run1000: a lost pre-action audit COMMIT never reaches or replays a mock WRITE."""

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


class _CommitThenLoseAcknowledgement:
    """Commit the pre-action row, then fail before the caller receives it."""

    def __init__(self, connection):
        self._connection = connection
        self._pre_action_inserted = False
        self._lost = False

    def __enter__(self):
        self._connection.__enter__()
        return self

    def __exit__(self, *args):
        result = self._connection.__exit__(*args)
        if args[0] is None and self._pre_action_inserted and not self._lost:
            self._lost = True
            raise sqlite3.OperationalError(
                "synthetic lost pre-action audit COMMIT acknowledgement"
            )
        return result

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


def test_lost_pre_action_audit_commit_blocks_backend_and_restart_replay(
    tmp_path, monkeypatch,
):
    (
        backend, registry, audit, occurrences, executor,
        call, grant, audit_path, occurrence_path,
    ) = _stack(tmp_path)
    token = OneShotAuthorization(
        "synthetic-audit-commit-unknown",
        call.request_id,
        500,
    )
    occurrence_id = "occ_" + "d" * 64

    original_connect = audit._connect
    monkeypatch.setattr(
        audit,
        "_connect",
        lambda **kwargs: _CommitThenLoseAcknowledgement(
            original_connect(**kwargs),
        ),
    )

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

    # The audit row and occurrence reservation both committed before the
    # caller lost the audit acknowledgement. The mock backend was never called.
    assert backend.calls == 0
    assert occurrences.count_synthetic() == 1

    reopened_audit = SQLiteActionAudit(audit_path, clock_ms=lambda: 101)
    reopened_occurrences = SyntheticOccurrenceStore(occurrence_path)
    assert [event.outcome for event in reopened_audit.events()] == [
        "mock_pre_action",
    ]

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
    assert [event.outcome for event in reopened_audit.events()] == [
        "mock_pre_action",
    ]
