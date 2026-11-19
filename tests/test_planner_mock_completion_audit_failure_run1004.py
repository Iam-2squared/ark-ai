"""Run1004: a post-mock completion-audit failure quarantines the Planner step."""

from __future__ import annotations

import pytest

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
    DisconnectedMockExecutionRejected,
    DisconnectedMockExecutor,
    MockToolBackend,
)
from ark.agency.durable_occurrence_review import SyntheticOccurrenceStore
from ark.agency.planner_journal import PlannerJournal
from ark.agency.planner_mock_cycle import (
    PlannerMockCycleRejected,
    execute_one_mock_step,
)


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
    audit = SQLiteActionAudit(
        tmp_path / "action-audit.sqlite3",
        clock_ms=lambda: 1_000,
    )
    occurrences = SyntheticOccurrenceStore(tmp_path / "occurrences.sqlite3")
    executor = DisconnectedMockExecutor(
        registry, PermissionGate(), audit, occurrences,
    )
    steps = (PlanStep("read", call),)
    journal = PlannerJournal(tmp_path / "planner-journal.sqlite3")
    journal.create_plan("fixture-plan", PlanGraph(steps))
    grants = (CapabilityGrant("capability.read", "synthetic:private"),)
    return backend, audit, registry, executor, journal, steps, grants


def test_completion_audit_failure_after_mock_call_quarantines_step_without_replay(
    tmp_path,
):
    backend, audit, registry, executor, journal, steps, grants = _stack(tmp_path)
    clock_calls = 0

    def fail_second_audit_clock_sample() -> int:
        nonlocal clock_calls
        clock_calls += 1
        if clock_calls == 2:
            raise RuntimeError("synthetic completion-audit clock failure")
        return 1_000 + clock_calls

    # The first audit append commits mock_pre_action. The second append fails
    # before its row is written, after the exact mock backend has already run.
    audit._clock_ms = fail_second_audit_clock_sample

    with pytest.raises(
        DisconnectedMockExecutionRejected,
        match="completion audit failed after mock-only execution",
    ):
        execute_one_mock_step(
            journal,
            "fixture-plan",
            steps,
            registry,
            executor,
            "read",
            grants,
            now_ms=10,
        )

    assert clock_calls == 2
    assert backend.calls == 1
    assert [event.outcome for event in audit.events()] == ["mock_pre_action"]

    recovered = journal.recover("fixture-plan", steps)
    assert recovered.sequence == 1
    assert recovered.ambiguous_running_step_ids == ("read",)
    assert recovered.graph.statuses()["read"].state is StepState.RUNNING
    assert recovered.graph.ready_steps() == ()
    assert recovered.dispatch_authorized is False
    assert recovered.automatic_replay_authorized is False

    with pytest.raises(
        PlannerMockCycleRejected,
        match="requested step is not currently ready",
    ):
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

    assert journal.recover("fixture-plan", steps).sequence == 1
    assert backend.calls == 1
    assert [event.outcome for event in audit.events()] == ["mock_pre_action"]
