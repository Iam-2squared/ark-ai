"""Disconnected regression checks for retained-history and post-startup SQLite drift."""

import hashlib
import sqlite3
from pathlib import Path

import pytest

from ark.agency.audit import SQLiteActionAudit
from ark.agency.contracts import (
    ActionAuditSchemaError,
    Effect,
    OneShotAuthorization,
    PlanStep,
    StepState,
    ToolCall,
)
from ark.agency.durable_occurrence_review import SyntheticOccurrenceStore
from ark.agency.planner_journal_review import (
    SyntheticPlanJournal,
    SyntheticPlanJournalRejected,
)
from ark.agency.registry import ToolRegistration, ToolRegistry


class NeverExecute:
    def execute(self, call: ToolCall) -> object:
        raise AssertionError("synthetic tests must not execute backends")


def _journal(path: Path) -> SyntheticPlanJournal:
    steps = (PlanStep("root", ToolCall("offline", "mock", "local", {"v": 1})),)
    return SyntheticPlanJournal(path, steps)


def _registry_and_token(name: str):
    registry = ToolRegistry(
        (ToolRegistration("offline", "mock", Effect.WRITE, "fixture", NeverExecute()),)
    )
    call = ToolCall("offline", "mock", "local", {"v": 1})
    token = OneShotAuthorization(name, call.request_id, 1000)
    occurrence = "occ_" + hashlib.sha256(name.encode("utf-8")).hexdigest()
    return registry, call, token, occurrence


def test_planner_retained_genesis_can_be_extended(tmp_path: Path):
    journal = _journal(tmp_path / "plan.sqlite")
    genesis = journal.recover().tail
    started = journal.append(
        "root", StepState.RUNNING, expected_revision=0, at_ms=10, retained=genesis
    )
    assert started.tail.event_count == 1
    finished = journal.append(
        "root", StepState.SUCCEEDED, expected_revision=1, at_ms=11, retained=genesis
    )
    assert finished.tail.event_count == 2
    assert journal.recover(retained=started.tail) == finished
    assert finished.dispatch_authorized is False


def test_planner_append_rejects_coordinated_history_truncation(tmp_path: Path):
    path = tmp_path / "plan.sqlite"
    journal = _journal(path)
    genesis = journal.recover()
    committed = journal.append(
        "root", StepState.RUNNING, expected_revision=0, at_ms=10
    )
    with sqlite3.connect(path) as conn:
        conn.execute("DELETE FROM synthetic_plan_events")
        conn.execute(
            """UPDATE synthetic_plan_header SET
               event_count=?,tail_hash=?,status_digest=?,last_at_ms=?""",
            (
                genesis.tail.event_count,
                genesis.tail.event_hash,
                genesis.tail.status_digest,
                genesis.tail.last_at_ms,
            ),
        )
    with pytest.raises(SyntheticPlanJournalRejected, match="retained.*history"):
        journal.append(
            "root", StepState.RUNNING, expected_revision=0,
            at_ms=12, retained=committed.tail,
        )
    assert journal.recover() == genesis


def test_planner_append_rejects_malformed_retained_tail(tmp_path: Path):
    journal = _journal(tmp_path / "plan.sqlite")
    with pytest.raises(SyntheticPlanJournalRejected, match="wrong type"):
        journal.append(
            "root", StepState.RUNNING, expected_revision=0,
            at_ms=10, retained=object(),
        )
    witness = journal.recover().tail
    object.__setattr__(witness, "event_count", True)
    with pytest.raises(SyntheticPlanJournalRejected, match="malformed"):
        journal.append(
            "root", StepState.RUNNING, expected_revision=0,
            at_ms=10, retained=witness,
        )
    assert journal.recover().tail.event_count == 0


@pytest.mark.parametrize("mutation", ["version", "ddl"])
def test_action_audit_read_rechecks_schema_after_startup(tmp_path: Path, mutation: str):
    path = tmp_path / "audit.sqlite"
    audit = SQLiteActionAudit(path, clock_ms=lambda: 10)
    call = ToolCall("offline", "mock", "local", {"v": 1})
    audit.append(call, outcome="synthetic")
    with sqlite3.connect(path) as conn:
        if mutation == "version":
            conn.execute("PRAGMA user_version=2")
        else:
            conn.execute("ALTER TABLE action_events ADD COLUMN injected TEXT")
    with pytest.raises(ActionAuditSchemaError, match="schema"):
        audit.events()


@pytest.mark.parametrize("mutation", ["version", "ddl"])
def test_action_audit_append_rechecks_schema_after_startup(tmp_path: Path, mutation: str):
    path = tmp_path / "audit.sqlite"
    audit = SQLiteActionAudit(path, clock_ms=lambda: 10)
    call = ToolCall("offline", "mock", "local", {"v": 1})
    with sqlite3.connect(path) as conn:
        if mutation == "version":
            conn.execute("PRAGMA user_version=2")
        else:
            conn.execute("ALTER TABLE action_events ADD COLUMN injected TEXT")
    with pytest.raises(ActionAuditSchemaError, match="schema"):
        audit.append(call, outcome="synthetic")
    with sqlite3.connect(path) as conn:
        assert conn.execute("SELECT COUNT(*) FROM action_events").fetchone()[0] == 0


def test_action_audit_normal_append_and_read_still_work(tmp_path: Path):
    audit = SQLiteActionAudit(tmp_path / "audit.sqlite", clock_ms=lambda: 10)
    call = ToolCall("offline", "mock", "local", {"v": 1})
    inserted = audit.append(call, outcome="synthetic")
    assert audit.events() == [inserted]


def test_synthetic_reserve_never_recreates_deleted_ledger(tmp_path: Path):
    path = tmp_path / "occ.sqlite"
    store = SyntheticOccurrenceStore(path)
    path.unlink()
    registry, call, token, occurrence = _registry_and_token("fake-token-1")
    with pytest.raises(sqlite3.OperationalError):
        store.reserve_synthetic(
            registry, call, token, occurrence_id=occurrence, now_ms=10
        )
    assert not path.exists()


def test_synthetic_reserve_never_recreates_moved_ledger(tmp_path: Path):
    path = tmp_path / "occ.sqlite"
    store = SyntheticOccurrenceStore(path)
    path.rename(tmp_path / "renamed.sqlite")
    registry, call, token, occurrence = _registry_and_token("fake-token-2")
    with pytest.raises(sqlite3.OperationalError):
        store.reserve_synthetic(
            registry, call, token, occurrence_id=occurrence, now_ms=10
        )
    assert not path.exists()


def test_synthetic_reserve_normal_uri_special_path(tmp_path: Path):
    path = tmp_path / "occ #1 %.sqlite"
    store = SyntheticOccurrenceStore(path)
    registry, call, token, occurrence = _registry_and_token("fake-token-3")
    receipt = store.reserve_synthetic(
        registry, call, token, occurrence_id=occurrence, now_ms=10
    )
    assert receipt.dispatch_authorized is False
    assert receipt.automatic_replay_authorized is False
    assert store.count_synthetic() == 1
