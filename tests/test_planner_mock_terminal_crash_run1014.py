"""Run1014: process death on either side of the Planner terminal COMMIT.

A disconnected mock WRITE completes its occurrence and audit sequence before
the Planner attempts SUCCEEDED. A hard exit around that final COMMIT must be
recovered as either ambiguous RUNNING or durable SUCCEEDED, never auto-replayed.
"""

from __future__ import annotations

import itertools
import multiprocessing
import os
import sqlite3
from contextlib import closing
from pathlib import Path

import pytest

from ark.agency import (
    CapabilityGrant,
    Effect,
    OneShotAuthorization,
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
from ark.agency.planner_journal import PlannerJournal
from ark.agency.planner_mock_cycle import (
    PlannerMockCycleRejected,
    execute_one_mock_step,
)

_PLAN_ID = "terminal-crash-plan"
_STEP_ID = "write"
_TOKEN_ID = "synthetic-terminal-crash-token"
_OCCURRENCE_ID = "occ_" + "d" * 64


def _make_stack(journal_path, audit_path, occurrence_path, *, create_plan):
    backend = MockToolBackend()
    call = ToolCall(
        "fixture.write",
        "capability.write",
        "synthetic:private",
        {"value": "fixture-only"},
    )
    registry = ToolRegistry((
        ToolRegistration(
            "fixture.write",
            "capability.write",
            Effect.WRITE,
            "ark.mock.fixture.v1",
            backend,
        ),
    ))
    gate = PermissionGate()
    ticks = itertools.count(1_000)
    audit = SQLiteActionAudit(audit_path, clock_ms=lambda: next(ticks))
    occurrences = SyntheticOccurrenceStore(occurrence_path)
    executor = DisconnectedMockExecutor(registry, gate, audit, occurrences)
    steps = (PlanStep(_STEP_ID, call),)
    journal = PlannerJournal(journal_path)
    grants = (CapabilityGrant("capability.write", "synthetic:private"),)
    if create_plan:
        journal.create_plan(_PLAN_ID, PlanGraph(steps))
    return backend, registry, audit, occurrences, executor, journal, steps, grants, call


def _crash_at_terminal_commit(
    journal_path: str,
    audit_path: str,
    occurrence_path: str,
    marker_path: str,
    phase: str,
) -> None:
    backend, registry, _, _, executor, journal, steps, grants, call = _make_stack(
        Path(journal_path),
        Path(audit_path),
        Path(occurrence_path),
        create_plan=False,
    )
    pinned_journal_path = str(Path(journal_path).absolute())
    commit_count = [0]
    original_connect = sqlite3.connect

    class _TerminalCommitBoundary:
        def __init__(self, connection):
            self._connection = connection

        def execute(self, statement, *args):
            is_commit = (
                type(statement) is str
                and statement.strip().upper() == "COMMIT"
            )
            if is_commit:
                commit_count[0] += 1
                if commit_count[0] == 2 and phase == "before":
                    Path(marker_path).write_text(
                        f"planner_commits=2;mock_calls={backend.calls}",
                        encoding="ascii",
                    )
                    os._exit(73)
            cursor = self._connection.execute(statement, *args)
            if is_commit and commit_count[0] == 2 and phase == "after":
                Path(marker_path).write_text(
                    f"planner_commits=2;mock_calls={backend.calls}",
                    encoding="ascii",
                )
                os._exit(74)
            return cursor

        def __getattr__(self, name):
            return getattr(self._connection, name)

    def connect(*args, **kwargs):
        database = args[0] if args else kwargs.get("database")
        connection = original_connect(*args, **kwargs)
        if type(database) is str and database == pinned_journal_path:
            return _TerminalCommitBoundary(connection)
        return connection

    # Patch only this spawned process and only the Planner journal database.
    # The first Planner COMMIT is RUNNING; the second is SUCCEEDED. The mock
    # executor's independent audit/occurrence databases remain unwrapped.
    sqlite3.connect = connect
    token = OneShotAuthorization(_TOKEN_ID, call.request_id, 500)
    execute_one_mock_step(
        journal,
        _PLAN_ID,
        steps,
        registry,
        executor,
        _STEP_ID,
        grants,
        now_ms=100,
        one_shot=token,
        occurrence_id=_OCCURRENCE_ID,
    )
    os._exit(99)


@pytest.mark.parametrize(
    ("phase", "exit_code", "expected_sequence", "expected_state", "ambiguous"),
    (
        ("before", 73, 1, StepState.RUNNING, (_STEP_ID,)),
        ("after", 74, 2, StepState.SUCCEEDED, ()),
    ),
)
def test_mock_completion_before_terminal_commit_is_never_auto_replayed(
    tmp_path: Path,
    phase: str,
    exit_code: int,
    expected_sequence: int,
    expected_state: StepState,
    ambiguous: tuple[str, ...],
) -> None:
    journal_path = tmp_path / "planner.sqlite3"
    audit_path = tmp_path / "audit.sqlite3"
    occurrence_path = tmp_path / "occurrences.sqlite3"
    marker_path = tmp_path / f"terminal-{phase}.marker"
    _make_stack(
        journal_path,
        audit_path,
        occurrence_path,
        create_plan=True,
    )

    process = multiprocessing.get_context("spawn").Process(
        target=_crash_at_terminal_commit,
        args=(
            str(journal_path),
            str(audit_path),
            str(occurrence_path),
            str(marker_path),
            phase,
        ),
    )
    process.start()
    process.join(timeout=40)
    if process.is_alive():
        process.terminate()
        process.join(timeout=5)

    assert process.exitcode == exit_code
    assert marker_path.read_text(encoding="ascii") == (
        "planner_commits=2;mock_calls=1"
    )

    journal = PlannerJournal(journal_path)
    recovered = journal.recover(
        _PLAN_ID,
        (PlanStep(
            _STEP_ID,
            ToolCall(
                "fixture.write",
                "capability.write",
                "synthetic:private",
                {"value": "fixture-only"},
            ),
        ),),
    )
    status = recovered.graph.statuses()[_STEP_ID]
    assert recovered.sequence == expected_sequence
    assert recovered.ambiguous_running_step_ids == ambiguous
    assert status.state is expected_state
    assert recovered.dispatch_authorized is False
    assert recovered.automatic_replay_authorized is False

    audit = SQLiteActionAudit(audit_path, clock_ms=lambda: 2_000)
    assert tuple(event.outcome for event in audit.events()) == (
        "mock_pre_action",
        "mock_completed",
    )
    occurrences = SyntheticOccurrenceStore(occurrence_path)
    assert occurrences.count_synthetic() == 1

    # A fresh process-local gate/backend cannot turn a RUNNING or SUCCEEDED
    # journal state into a retryable step. The old occurrence/audit evidence
    # remains unchanged, and the new mock backend is never called.
    (
        retry_backend,
        retry_registry,
        retry_audit,
        retry_occurrences,
        retry_executor,
        retry_journal,
        retry_steps,
        retry_grants,
        retry_call,
    ) = _make_stack(
        journal_path,
        audit_path,
        occurrence_path,
        create_plan=False,
    )
    with pytest.raises(PlannerMockCycleRejected, match="not currently ready"):
        execute_one_mock_step(
            retry_journal,
            _PLAN_ID,
            retry_steps,
            retry_registry,
            retry_executor,
            _STEP_ID,
            retry_grants,
            now_ms=200,
            one_shot=OneShotAuthorization(_TOKEN_ID, retry_call.request_id, 500),
            occurrence_id=_OCCURRENCE_ID,
        )
    assert retry_backend.calls == 0
    assert tuple(event.outcome for event in retry_audit.events()) == (
        "mock_pre_action",
        "mock_completed",
    )
    assert retry_occurrences.count_synthetic() == 1
    assert retry_journal.recover(_PLAN_ID, retry_steps).sequence == expected_sequence

    for database in (journal_path, audit_path, occurrence_path):
        with closing(sqlite3.connect(database)) as connection:
            assert connection.execute("PRAGMA quick_check").fetchone() == ("ok",)
