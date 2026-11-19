"""Run999: uncertain Planner terminal commit never replays a completed mock step."""

from __future__ import annotations

import itertools
import sqlite3

import pytest

import ark.agency.planner_journal as journal_module
from ark.agency import (
    CapabilityGrant,
    Effect,
    PermissionGate,
    PlanGraph,
    PlanStep,
    SQLiteActionAudit,
    StepState,
    ToolCall,
    ToolRegistration,
    ToolRegistry,
)
from ark.agency.disconnected_mock_executor import (
    DisconnectedMockExecutor,
    MockToolBackend,
)
from ark.agency.durable_occurrence_review import SyntheticOccurrenceStore
from ark.agency.planner_journal import (
    PlannerJournal,
    PlannerJournalCommitUnknown,
)
from ark.agency.planner_mock_cycle import (
    PlannerMockCycleRejected,
    execute_one_mock_step,
)


class _LoseSucceededCommitAcknowledgement:
    """Persist or roll back SUCCEEDED, then expose only an uncertain COMMIT error."""

    def __init__(self, connection, *, commit_persists: bool):
        self._connection = connection
        self._commit_persists = commit_persists
        self._succeeded_event_pending = False

    def execute(self, statement, *args):
        if (
            type(statement) is str
            and statement.strip().upper() == "COMMIT"
            and self._succeeded_event_pending
        ):
            self._succeeded_event_pending = False
            if self._commit_persists:
                self._connection.execute(statement, *args)
            else:
                self._connection.execute("ROLLBACK")
            raise sqlite3.OperationalError(
                "synthetic uncertain SUCCEEDED COMMIT acknowledgement"
            )

        cursor = self._connection.execute(statement, *args)
        if (
            type(statement) is str
            and statement.startswith("INSERT INTO planner_journal_events")
        ):
            parameters = args[0] if args else ()
            if (
                type(parameters) is tuple
                and len(parameters) >= 5
                and parameters[4] == StepState.SUCCEEDED.value
            ):
                self._succeeded_event_pending = True
        return cursor

    def __getattr__(self, name):
        return getattr(self._connection, name)


def _stack(tmp_path):
    backend = MockToolBackend()
    call = ToolCall(
        "fixture.read",
        "capability.read",
        "synthetic:private",
        {"value": "read"},
    )
    registry = ToolRegistry((
        ToolRegistration(
            "fixture.read",
            "capability.read",
            Effect.READ,
            "ark.mock.fixture.v1",
            backend,
        ),
    ))
    gate = PermissionGate()
    ticks = itertools.count(1_000)
    audit = SQLiteActionAudit(
        tmp_path / "action-audit.sqlite3",
        clock_ms=lambda: next(ticks),
    )
    occurrences = SyntheticOccurrenceStore(tmp_path / "occurrences.sqlite3")
    executor = DisconnectedMockExecutor(registry, gate, audit, occurrences)
    steps = (PlanStep("read", call),)
    journal = PlannerJournal(tmp_path / "planner-journal.sqlite3")
    journal.create_plan("fixture-plan", PlanGraph(steps))
    grants = (CapabilityGrant("capability.read", "synthetic:private"),)
    return backend, audit, occurrences, executor, journal, steps, grants


@pytest.mark.parametrize("commit_persists", (True, False))
def test_uncertain_succeeded_commit_recovers_without_mock_replay(
    tmp_path, monkeypatch, commit_persists: bool,
):
    backend, audit, occurrences, executor, journal, steps, grants = _stack(tmp_path)
    real_connect = sqlite3.connect

    def connect(database, *args, **kwargs):
        connection = real_connect(database, *args, **kwargs)
        if str(database) == journal._path:
            return _LoseSucceededCommitAcknowledgement(
                connection,
                commit_persists=commit_persists,
            )
        return connection

    # Only the Planner journal connection is fault-injected. Audit and
    # occurrence ledgers remain independent disposable SQLite fixtures.
    monkeypatch.setattr(journal_module.sqlite3, "connect", connect)

    with pytest.raises(
        PlannerJournalCommitUnknown,
        match="COMMIT outcome is unknown",
    ):
        execute_one_mock_step(
            journal,
            "fixture-plan",
            steps,
            ToolRegistry((
                ToolRegistration(
                    "fixture.read",
                    "capability.read",
                    Effect.READ,
                    "ark.mock.fixture.v1",
                    backend,
                ),
            )),
            executor,
            "read",
            grants,
            now_ms=10,
        )

    recovered = journal.recover("fixture-plan", steps)
    status = recovered.graph.statuses()["read"]
    if commit_persists:
        assert recovered.sequence == 2
        assert status.state is StepState.SUCCEEDED
        assert recovered.ambiguous_running_step_ids == ()
    else:
        assert recovered.sequence == 1
        assert status.state is StepState.RUNNING
        assert recovered.ambiguous_running_step_ids == ("read",)

    # Both possible durable outcomes are terminal for dispatch purposes:
    # neither a completed step nor an ambiguous RUNNING step is ready to replay.
    assert recovered.graph.ready_steps() == ()
    assert recovered.dispatch_authorized is False
    assert recovered.automatic_replay_authorized is False
    assert backend.calls == 1
    assert len(audit.events()) == 2
    assert occurrences.count_synthetic() == 0

    with pytest.raises(PlannerMockCycleRejected, match="not currently ready"):
        execute_one_mock_step(
            journal,
            "fixture-plan",
            steps,
            executor._registry,
            executor,
            "read",
            grants,
            now_ms=11,
        )

    assert journal.recover("fixture-plan", steps).graph.ready_steps() == ()
    assert backend.calls == 1
    assert len(audit.events()) == 2
    assert occurrences.count_synthetic() == 0
