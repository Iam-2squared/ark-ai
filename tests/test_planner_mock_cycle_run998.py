"""Run998: durable Planner transitions compose with the disconnected mock only."""

from __future__ import annotations

import itertools
import sqlite3

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
    read_call = ToolCall(
        "fixture.read",
        "capability.read",
        "synthetic:private",
        {"value": "read"},
    )
    write_call = ToolCall(
        "fixture.write",
        "capability.write",
        "synthetic:private",
        {"value": "write"},
    )
    registry = ToolRegistry((
        ToolRegistration(
            "fixture.read",
            "capability.read",
            Effect.READ,
            "ark.mock.fixture.v1",
            backend,
        ),
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
    audit_path = tmp_path / "action-audit.sqlite3"
    occurrence_path = tmp_path / "occurrences.sqlite3"
    audit = SQLiteActionAudit(audit_path, clock_ms=lambda: next(ticks))
    occurrences = SyntheticOccurrenceStore(occurrence_path)
    executor = DisconnectedMockExecutor(registry, gate, audit, occurrences)
    steps = (
        PlanStep("read", read_call),
        PlanStep("write", write_call, ("read",)),
    )
    journal = PlannerJournal(tmp_path / "planner-journal.sqlite3")
    journal.create_plan("fixture-plan", PlanGraph(steps))
    grants = (
        CapabilityGrant("capability.read", "synthetic:private"),
        CapabilityGrant("capability.write", "synthetic:private"),
    )
    return (
        backend, registry, audit, occurrences, executor, journal,
        steps, read_call, write_call, grants, audit_path,
    )


def test_one_step_cycles_advance_only_after_mock_and_durable_terminal_receipt(
    tmp_path,
):
    (
        backend, registry, audit, occurrences, executor, journal,
        steps, _, write_call, grants, _,
    ) = _stack(tmp_path)

    read = execute_one_mock_step(
        journal, "fixture-plan", steps, registry, executor,
        "read", grants, now_ms=10,
    )
    assert (read.sequence_before, read.running_sequence, read.completed_sequence) == (
        0, 1, 2,
    )
    assert read.mock_receipt.effect is Effect.READ
    assert read.mock_receipt.occurrence_id is None
    assert read.mock_only is True
    assert read.dispatch_authorized is False
    assert read.automatic_replay_authorized is False
    assert read.external_effect_proven is False
    assert backend.calls == 1

    token = OneShotAuthorization(
        "synthetic-write-token",
        write_call.request_id,
        500,
    )
    occurrence = "occ_" + "e" * 64
    write = execute_one_mock_step(
        journal, "fixture-plan", steps, registry, executor,
        "write", grants, now_ms=11,
        one_shot=token,
        occurrence_id=occurrence,
    )
    assert (write.sequence_before, write.running_sequence, write.completed_sequence) == (
        2, 3, 4,
    )
    assert write.mock_receipt.effect is Effect.WRITE
    assert write.mock_receipt.occurrence_id == occurrence
    assert write.journal_receipt.sequence == 4
    assert len(write.preflight_fingerprint) == 64
    assert write.registry_revision == registry.revision
    assert write.bound_action_id == write.mock_receipt.bound_action_id
    assert backend.calls == 2
    assert occurrences.count_synthetic() == 1
    assert [event.outcome for event in audit.events()] == [
        "mock_pre_action", "mock_completed",
        "mock_pre_action", "mock_completed",
    ]

    recovered = journal.recover("fixture-plan", steps)
    statuses = recovered.graph.statuses()
    assert recovered.sequence == 4
    assert recovered.ambiguous_running_step_ids == ()
    assert statuses["read"].state is StepState.SUCCEEDED
    assert statuses["write"].state is StepState.SUCCEEDED
    assert recovered.dispatch_authorized is False
    assert recovered.automatic_replay_authorized is False
    assert write.mock_receipt.exact_once_external_effect_proven is False


def test_non_ready_dependent_step_is_rejected_before_any_journal_or_mock_write(
    tmp_path,
):
    (
        backend, registry, audit, occurrences, executor, journal,
        steps, _, _, grants, _,
    ) = _stack(tmp_path)

    with pytest.raises(PlannerMockCycleRejected, match="not currently ready"):
        execute_one_mock_step(
            journal, "fixture-plan", steps, registry, executor,
            "write", grants, now_ms=10,
            one_shot=OneShotAuthorization(
                "unused-token", steps[1].call.request_id, 500,
            ),
            occurrence_id="occ_" + "f" * 64,
        )

    recovered = journal.recover("fixture-plan", steps)
    assert recovered.sequence == 0
    assert recovered.graph.statuses()["read"].state is StepState.PENDING
    assert recovered.graph.statuses()["write"].state is StepState.PENDING
    assert backend.calls == 0
    assert audit.events() == []
    assert occurrences.count_synthetic() == 0


def test_executor_failure_after_running_is_ambiguous_and_never_auto_replayed(
    tmp_path,
):
    (
        backend, registry, audit, occurrences, executor, journal,
        steps, read_call, _, grants, audit_path,
    ) = _stack(tmp_path)

    # Create a local audit high-water gap. The mock executor must fail its
    # pre-action audit before the backend is called.
    audit.append(read_call, outcome="seed")
    with sqlite3.connect(audit_path) as connection:
        connection.execute("DELETE FROM action_events")

    with pytest.raises(
        DisconnectedMockExecutionRejected,
        match="pre-action audit failed; mock backend was not called",
    ):
        execute_one_mock_step(
            journal, "fixture-plan", steps, registry, executor,
            "read", grants, now_ms=10,
        )

    recovered = journal.recover("fixture-plan", steps)
    assert recovered.sequence == 1
    assert recovered.ambiguous_running_step_ids == ("read",)
    assert recovered.graph.statuses()["read"].state is StepState.RUNNING
    assert recovered.graph.ready_steps() == ()
    assert recovered.automatic_replay_authorized is False
    assert backend.calls == 0
    assert occurrences.count_synthetic() == 0

    with pytest.raises(PlannerMockCycleRejected, match="not currently ready"):
        execute_one_mock_step(
            journal, "fixture-plan", steps, registry, executor,
            "read", grants, now_ms=11,
        )
    assert journal.recover("fixture-plan", steps).sequence == 1
    assert backend.calls == 0


def test_read_step_rejects_write_authorization_before_running(tmp_path):
    (
        backend, registry, audit, occurrences, executor, journal,
        steps, read_call, _, grants, _,
    ) = _stack(tmp_path)

    with pytest.raises(
        PlannerMockCycleRejected,
        match="READ steps cannot carry WRITE authorization inputs",
    ):
        execute_one_mock_step(
            journal, "fixture-plan", steps, registry, executor,
            "read", grants, now_ms=10,
            one_shot=OneShotAuthorization(
                "wrong-effect-token", read_call.request_id, 500,
            ),
            occurrence_id="occ_" + "a" * 64,
        )

    assert journal.recover("fixture-plan", steps).sequence == 0
    assert backend.calls == 0
    assert audit.events() == []
    assert occurrences.count_synthetic() == 0


def test_non_mock_registry_backend_is_rejected_before_running_or_audit(tmp_path):
    class ExternalLikeBackend:
        def __init__(self):
            self.calls = 0

        def execute(self, _call):
            self.calls += 1
            raise AssertionError("external-like backend must never be called")

    backend = ExternalLikeBackend()
    call = ToolCall(
        "fixture.external-like",
        "capability.read",
        "synthetic:private",
        {"value": "must-not-dispatch"},
    )
    registry = ToolRegistry((
        ToolRegistration(
            "fixture.external-like",
            "capability.read",
            Effect.READ,
            "not-a-mock-backend",
            backend,
        ),
    ))
    audit = SQLiteActionAudit(
        tmp_path / "external-like-audit.sqlite3",
        clock_ms=lambda: 100,
    )
    executor = DisconnectedMockExecutor(registry, PermissionGate(), audit)
    steps = (PlanStep("root", call),)
    journal = PlannerJournal(tmp_path / "external-like-planner.sqlite3")
    journal.create_plan("external-like-plan", PlanGraph(steps))

    with pytest.raises(
        PlannerMockCycleRejected,
        match="only the exact disconnected mock backend",
    ):
        execute_one_mock_step(
            journal,
            "external-like-plan",
            steps,
            registry,
            executor,
            "root",
            (CapabilityGrant("capability.read", "synthetic:private"),),
            now_ms=10,
        )

    assert journal.recover("external-like-plan", steps).sequence == 0
    assert backend.calls == 0
    assert audit.events() == []
