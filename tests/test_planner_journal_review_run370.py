"""Reversible SQLite plan transition journal: exact replay, no tool execution."""

import sqlite3
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from threading import Barrier

import pytest

from ark.agency.contracts import PlanConflictError, PlanStep, StepState, ToolCall
from ark.agency.planner_journal_review import (
    SyntheticPlanJournal,
    SyntheticPlanJournalRejected,
)


def _steps(value=1):
    return (
        PlanStep("root", ToolCall("fixture", "offline", "local", {"n": value})),
        PlanStep(
            "child",
            ToolCall("fixture", "offline", "local", {"n": 2}),
            ("root",),
        ),
    )


def _journal(path: Path):
    return SyntheticPlanJournal(path, _steps())


def test_empty_recovery_is_stable_and_disconnected(tmp_path: Path):
    path = tmp_path / "journal.sqlite"
    journal = _journal(path)
    snapshot = journal.recover()
    assert snapshot.tail.event_count == 0
    assert snapshot.tail.last_at_ms == -1
    assert snapshot.ambiguous_running_steps == ()
    assert snapshot.dispatch_authorized is False
    assert snapshot.automatic_replay_authorized is False
    assert snapshot.step_statuses == (
        ("child", "pending", 0),
        ("root", "pending", 0),
    )
    assert _journal(path).recover() == snapshot


def test_replay_preserves_explicit_transitions_and_derived_blocks(tmp_path: Path):
    path = tmp_path / "journal.sqlite"
    journal = _journal(path)
    first = journal.append("root", StepState.RUNNING, expected_revision=0, at_ms=10)
    assert first.ambiguous_running_steps == ("root",)
    second = journal.append("root", StepState.FAILED, expected_revision=1, at_ms=11)
    assert second.tail.event_count == 2
    assert second.step_statuses == (
        ("child", "blocked", 1),
        ("root", "failed", 2),
    )
    assert second.ambiguous_running_steps == ()
    assert _journal(path).recover(retained=first.tail) == second


def test_running_after_crash_is_unknown_not_automatically_replayed(tmp_path: Path):
    path = tmp_path / "journal.sqlite"
    journal = _journal(path)
    committed = journal.append("root", StepState.RUNNING, expected_revision=0, at_ms=7)
    del journal
    reloaded = _journal(path).recover(retained=committed.tail)
    assert reloaded.ambiguous_running_steps == ("root",)
    assert reloaded.automatic_replay_authorized is False
    assert reloaded.dispatch_authorized is False


def test_transition_cas_rejects_stale_revision_without_append(tmp_path: Path):
    journal = _journal(tmp_path / "journal.sqlite")
    journal.append("root", StepState.RUNNING, expected_revision=0, at_ms=4)
    before = journal.recover()
    with pytest.raises(PlanConflictError, match="revision"):
        journal.append("root", StepState.SUCCEEDED, expected_revision=0, at_ms=5)
    assert journal.recover() == before


def test_write_crash_semantics_are_atomic_under_failing_transition(tmp_path: Path):
    journal = _journal(tmp_path / "journal.sqlite")
    before = journal.recover()
    with pytest.raises(PlanConflictError, match="dependencies"):
        journal.append("child", StepState.RUNNING, expected_revision=0, at_ms=1)
    assert journal.recover() == before


@pytest.mark.parametrize("bad", [-1, True, "9", 2**63])
def test_bad_timestamp_rejected_before_write(tmp_path: Path, bad):
    journal = _journal(tmp_path / "journal.sqlite")
    with pytest.raises(SyntheticPlanJournalRejected, match="timestamp"):
        journal.append("root", StepState.RUNNING, expected_revision=0, at_ms=bad)
    assert journal.recover().tail.event_count == 0


def test_clock_regression_does_not_commit(tmp_path: Path):
    journal = _journal(tmp_path / "journal.sqlite")
    journal.append("root", StepState.RUNNING, expected_revision=0, at_ms=10)
    before = journal.recover()
    with pytest.raises(SyntheticPlanJournalRejected, match="clock regression"):
        journal.append("root", StepState.SUCCEEDED, expected_revision=1, at_ms=9)
    assert journal.recover() == before


def test_same_clock_value_is_allowed_for_distinct_transitions(tmp_path: Path):
    journal = _journal(tmp_path / "journal.sqlite")
    journal.append("root", StepState.RUNNING, expected_revision=0, at_ms=10)
    last = journal.append("root", StepState.SUCCEEDED, expected_revision=1, at_ms=10)
    assert last.tail.event_count == 2
    assert last.tail.last_at_ms == 10


def test_event_rewrite_fails_hash_chain(tmp_path: Path):
    path = tmp_path / "journal.sqlite"
    journal = _journal(path)
    journal.append("root", StepState.RUNNING, expected_revision=0, at_ms=10)
    with sqlite3.connect(path) as conn:
        conn.execute(
            "UPDATE synthetic_plan_events SET occurred_at_ms=11 WHERE seq=1"
        )
    with pytest.raises(SyntheticPlanJournalRejected, match="chain"):
        journal.recover()


def test_coordinated_tail_truncation_requires_retained_witness(tmp_path: Path):
    path = tmp_path / "journal.sqlite"
    journal = _journal(path)
    prefix = journal.append("root", StepState.RUNNING, expected_revision=0, at_ms=10)
    later = journal.append("root", StepState.SUCCEEDED, expected_revision=1, at_ms=11)
    with sqlite3.connect(path) as conn:
        conn.execute("DELETE FROM synthetic_plan_events WHERE seq=2")
        conn.execute(
            """UPDATE synthetic_plan_header
               SET event_count=?,tail_hash=?,status_digest=?,last_at_ms=?""",
            (
                prefix.tail.event_count, prefix.tail.event_hash,
                prefix.tail.status_digest, prefix.tail.last_at_ms,
            ),
        )
    # A local self-consistency check cannot attest against a coordinated
    # truncation. Only the independently retained later witness detects it.
    assert journal.recover().tail == prefix.tail
    with pytest.raises(SyntheticPlanJournalRejected, match="retained.*history"):
        journal.recover(retained=later.tail)


def test_changed_topology_and_arguments_are_rejected(tmp_path: Path):
    path = tmp_path / "journal.sqlite"
    _journal(path)
    with pytest.raises(SyntheticPlanJournalRejected, match="header integrity"):
        SyntheticPlanJournal(path, _steps(99))


def test_schema_drift_is_rejected_without_migration(tmp_path: Path):
    path = tmp_path / "journal.sqlite"
    journal = _journal(path)
    with sqlite3.connect(path) as conn:
        conn.execute("ALTER TABLE synthetic_plan_events ADD COLUMN corrupt TEXT")
    with pytest.raises(SyntheticPlanJournalRejected, match="schema changed"):
        journal.recover()
    with pytest.raises(SyntheticPlanJournalRejected, match="schema changed"):
        _journal(path)


def test_missing_file_is_not_created_by_recovery(tmp_path: Path):
    path = tmp_path / "journal.sqlite"
    journal = _journal(path)
    path.unlink()
    with pytest.raises(sqlite3.OperationalError):
        journal.recover()
    assert not path.exists()


def test_unversioned_occupied_database_is_not_repaired(tmp_path: Path):
    path = tmp_path / "journal.sqlite"
    with sqlite3.connect(path) as conn:
        conn.execute("CREATE TABLE unrelated(value TEXT)")
    with pytest.raises(SyntheticPlanJournalRejected, match="not empty"):
        _journal(path)
    with sqlite3.connect(path) as conn:
        assert conn.execute("SELECT name FROM sqlite_master").fetchone()[0] == "unrelated"


def test_exact_retained_tail_type_and_shape_are_required(tmp_path: Path):
    journal = _journal(tmp_path / "journal.sqlite")
    witness = journal.recover().tail
    with pytest.raises(SyntheticPlanJournalRejected, match="wrong type"):
        journal.recover(retained=object())
    object.__setattr__(witness, "event_count", True)
    with pytest.raises(SyntheticPlanJournalRejected, match="malformed"):
        journal.recover(retained=witness)


def test_two_instances_racing_same_revision_only_commit_once(tmp_path: Path):
    path = tmp_path / "journal.sqlite"
    first, second = _journal(path), _journal(path)
    barrier = Barrier(2)

    def attempt(journal):
        barrier.wait(timeout=5)
        try:
            journal.append("root", StepState.RUNNING, expected_revision=0, at_ms=10)
            return True
        except PlanConflictError:
            return False

    with ThreadPoolExecutor(max_workers=2) as pool:
        outcomes = list(pool.map(attempt, (first, second)))
    assert sorted(outcomes) == [False, True]
    assert first.recover().tail.event_count == 1


def test_uri_special_characters_are_readonly_safe(tmp_path: Path):
    path = tmp_path / "journal #1 %.sqlite"
    journal = _journal(path)
    assert journal.recover().tail.event_count == 0
