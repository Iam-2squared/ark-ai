"""Run994: append-only Planner journal and crash-recovery invariants."""

from __future__ import annotations

import sqlite3
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from threading import Barrier

import pytest

from ark.agency.contracts import PlanStep, StepState, ToolCall
from ark.agency.planner import PlanGraph
from ark.agency.planner_journal import (
    PlannerJournal,
    PlannerJournalConflictError,
    PlannerJournalCorruptError,
    PlannerJournalNotFoundError,
    PlannerJournalSchemaError,
)


def _steps() -> tuple[PlanStep, ...]:
    return (
        PlanStep(
            "root",
            ToolCall(
                "fixture.root",
                "fixture.read",
                "synthetic:private",
                {"private_fixture": "raw-sensitive-fixture"},
            ),
        ),
        PlanStep(
            "child",
            ToolCall(
                "fixture.child",
                "fixture.read",
                "synthetic:private",
                {"value": "child"},
            ),
            ("root",),
        ),
    )


def _journal(tmp_path: Path) -> tuple[PlannerJournal, Path]:
    path = tmp_path / "planner-journal.sqlite3"
    return PlannerJournal(path), path


def test_genesis_and_cold_recovery_are_content_minimized(tmp_path):
    journal, path = _journal(tmp_path)
    steps = _steps()
    graph = PlanGraph(steps)

    receipt = journal.create_plan("fixture-plan", graph)
    recovered = journal.recover("fixture-plan", steps)

    assert receipt.sequence == 0
    assert receipt.dispatch_authorized is False
    assert receipt.automatic_replay_authorized is False
    assert recovered.sequence == 0
    assert recovered.last_event_hash == receipt.event_hash
    assert recovered.ambiguous_running_step_ids == ()
    assert all(
        status.state is StepState.PENDING and status.revision == 0
        for status in recovered.graph.statuses().values()
    )
    assert recovered.dispatch_authorized is False
    assert recovered.automatic_replay_authorized is False
    assert b"raw-sensitive-fixture" not in path.read_bytes()


def test_transition_is_durable_and_terminal_failure_blocks_descendants(tmp_path):
    journal, _ = _journal(tmp_path)
    steps = _steps()
    graph = PlanGraph(steps)
    journal.create_plan("terminal-plan", graph)

    running = journal.transition(
        "terminal-plan",
        graph,
        "root",
        StepState.RUNNING,
        expected_revision=0,
        expected_sequence=0,
    )
    failed = journal.transition(
        "terminal-plan",
        running.graph,
        "root",
        StepState.FAILED,
        expected_revision=1,
        expected_sequence=1,
    )
    recovered = journal.recover("terminal-plan", steps)
    statuses = recovered.graph.statuses()

    assert failed.receipt.sequence == 2
    assert statuses["root"].state is StepState.FAILED
    assert statuses["root"].revision == 2
    assert statuses["child"].state is StepState.BLOCKED
    assert statuses["child"].revision == 1
    assert recovered.sequence == 2
    assert recovered.ambiguous_running_step_ids == ()


def test_running_state_is_reported_as_ambiguous_not_replayed(tmp_path):
    journal, _ = _journal(tmp_path)
    steps = _steps()
    graph = PlanGraph(steps)
    journal.create_plan("ambiguous-plan", graph)
    result = journal.transition(
        "ambiguous-plan",
        graph,
        "root",
        StepState.RUNNING,
        expected_revision=0,
        expected_sequence=0,
    )

    recovered = journal.recover("ambiguous-plan", steps)

    assert result.graph.statuses()["root"].state is StepState.RUNNING
    assert recovered.ambiguous_running_step_ids == ("root",)
    assert recovered.graph.statuses()["root"].state is StepState.RUNNING
    assert recovered.graph.ready_steps() == ()
    assert recovered.automatic_replay_authorized is False


def test_stale_graph_and_stale_sequence_cannot_append(tmp_path):
    journal, _ = _journal(tmp_path)
    steps = _steps()
    initial = PlanGraph(steps)
    journal.create_plan("cas-plan", initial)
    first = journal.transition(
        "cas-plan",
        initial,
        "root",
        StepState.RUNNING,
        expected_revision=0,
        expected_sequence=0,
    )

    with pytest.raises(PlannerJournalConflictError, match="stale"):
        journal.transition(
            "cas-plan",
            initial,
            "root",
            StepState.CANCELLED,
            expected_revision=0,
            expected_sequence=1,
        )

    with pytest.raises(PlannerJournalConflictError, match="sequence"):
        journal.transition(
            "cas-plan",
            first.graph,
            "root",
            StepState.SUCCEEDED,
            expected_revision=1,
            expected_sequence=0,
        )

    assert journal.recover("cas-plan", steps).sequence == 1


def test_illegal_transition_does_not_append_an_event(tmp_path):
    journal, _ = _journal(tmp_path)
    steps = _steps()
    graph = PlanGraph(steps)
    journal.create_plan("illegal-plan", graph)

    with pytest.raises(PlannerJournalConflictError, match="rejected"):
        journal.transition(
            "illegal-plan",
            graph,
            "root",
            StepState.SUCCEEDED,
            expected_revision=0,
            expected_sequence=0,
        )

    assert journal.recover("illegal-plan", steps).sequence == 0


def test_two_connections_compare_and_swap_one_sequence(tmp_path):
    journal, path = _journal(tmp_path)
    steps = _steps()
    initial = PlanGraph(steps)
    journal.create_plan("race-plan", initial)
    barrier = Barrier(2)

    def append_from_independent_connection():
        independent = PlannerJournal(path)
        graph = independent.recover("race-plan", steps).graph
        barrier.wait(timeout=10)
        try:
            independent.transition(
                "race-plan",
                graph,
                "root",
                StepState.RUNNING,
                expected_revision=0,
                expected_sequence=0,
            )
            return "committed"
        except PlannerJournalConflictError:
            return "conflict"

    with ThreadPoolExecutor(max_workers=2) as pool:
        outcomes = list(pool.map(lambda _: append_from_independent_connection(), range(2)))

    assert sorted(outcomes) == ["committed", "conflict"]
    recovered = journal.recover("race-plan", steps)
    assert recovered.sequence == 1
    assert recovered.graph.statuses()["root"].state is StepState.RUNNING


def test_event_hash_tampering_fails_closed(tmp_path):
    journal, path = _journal(tmp_path)
    steps = _steps()
    graph = PlanGraph(steps)
    journal.create_plan("tamper-plan", graph)
    journal.transition(
        "tamper-plan",
        graph,
        "root",
        StepState.RUNNING,
        expected_revision=0,
        expected_sequence=0,
    )

    with sqlite3.connect(path) as connection:
        connection.execute(
            "UPDATE planner_journal_events SET to_state = 'cancelled' "
            "WHERE plan_id = 'tamper-plan' AND sequence = 1"
        )

    with pytest.raises(PlannerJournalCorruptError, match="digest mismatch"):
        journal.recover("tamper-plan", steps)


def test_wrong_plan_topology_is_rejected(tmp_path):
    journal, _ = _journal(tmp_path)
    steps = _steps()
    journal.create_plan("topology-plan", PlanGraph(steps))
    changed = (
        steps[0],
        PlanStep(
            "child",
            ToolCall(
                "fixture.child",
                "fixture.read",
                "synthetic:private",
                {"value": "changed"},
            ),
            ("root",),
        ),
    )

    with pytest.raises(PlannerJournalCorruptError, match="topology"):
        journal.recover("topology-plan", changed)


def test_extra_schema_object_is_rejected(tmp_path):
    journal, path = _journal(tmp_path)
    with sqlite3.connect(path) as connection:
        connection.execute("CREATE TABLE unexpected_local_table (value TEXT)")

    with pytest.raises(PlannerJournalSchemaError, match="managed tables"):
        PlannerJournal(path)


def test_bad_plan_identity_is_rejected_before_database_access(tmp_path, monkeypatch):
    journal, _ = _journal(tmp_path)
    graph = PlanGraph(_steps())
    import ark.agency.planner_journal as module

    def forbidden_connect(*_args, **_kwargs):
        raise AssertionError("invalid identity must be rejected before SQLite open")

    monkeypatch.setattr(module.sqlite3, "connect", forbidden_connect)
    with pytest.raises(ValueError, match="control character"):
        journal.create_plan("bad\nplan", graph)


def test_new_genesis_rejects_a_graph_that_already_advanced(tmp_path):
    journal, _ = _journal(tmp_path)
    steps = _steps()
    graph = PlanGraph(steps)
    graph.transition("root", StepState.RUNNING, expected_revision=0)

    with pytest.raises(PlannerJournalConflictError, match="genesis"):
        journal.create_plan("not-genesis", graph)

    with pytest.raises(PlannerJournalNotFoundError):
        journal.recover("not-genesis", steps)
