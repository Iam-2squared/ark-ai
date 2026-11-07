"""Offline WRITE recovery must quarantine descendants across READ bridges.

No test invokes a real executor, starts a device, or interprets a local
receipt as authenticated outcome/permission. SQLite sources are disposable.
"""

import pytest

from ark.agency.audit import SQLiteActionAudit
from ark.agency.contracts import (
    Effect,
    OneShotAuthorization,
    PlanStep,
    StepState,
    ToolCall,
)
from ark.agency.durable_occurrence_review import SyntheticOccurrenceStore
from ark.agency.planner_journal_review import SyntheticPlanJournal
from ark.agency.registry import ToolRegistration, ToolRegistry
from ark.agency.synthetic_write_plan_recovery_review import (
    review_synthetic_write_plan,
)


class NoDispatch:
    def __init__(self):
        self.calls = 0

    def execute(self, _call):
        self.calls += 1
        raise AssertionError("local recovery diagnosis may never dispatch")


def _state(tmp_path, *, root_state, reserved_descendant):
    root = ToolCall("writer", "offline.write", "synthetic", {"step": "root"})
    read = ToolCall("reader", "offline.read", "synthetic", {"step": "bridge"})
    tail = ToolCall("writer", "offline.write", "synthetic", {"step": "tail"})
    leaf = ToolCall("writer", "offline.write", "synthetic", {"step": "leaf"})
    independent = ToolCall("writer", "offline.write", "synthetic", {"step": "other"})
    graph = (
        PlanStep("root", root),
        PlanStep("bridge", read, depends_on=("root",)),
        PlanStep("tail", tail, depends_on=("bridge",)),
        PlanStep("leaf", leaf, depends_on=("tail",)),
        PlanStep("independent", independent),
    )
    journal = SyntheticPlanJournal(tmp_path / "plan.sqlite", graph)
    ledger = SyntheticOccurrenceStore(tmp_path / "occurrences.sqlite")
    audit = SQLiteActionAudit(tmp_path / "audit.sqlite", clock_ms=lambda: 20)
    backend = NoDispatch()
    registry = ToolRegistry((
        ToolRegistration("writer", "offline.write", Effect.WRITE, "mock", backend),
        ToolRegistration("reader", "offline.read", Effect.READ, "mock", backend),
    ))
    journal.append("root", StepState.RUNNING, expected_revision=0, at_ms=10)
    if root_state == "failed":
        journal.append("root", StepState.FAILED, expected_revision=1, at_ms=11)
    if reserved_descendant:
        ledger.reserve_synthetic(
            registry, tail,
            OneShotAuthorization("offline-token", tail.request_id, 1000),
            occurrence_id="occ_" + "c" * 64,
            now_ms=12,
        )
    return journal, ledger._path, audit, registry, backend


@pytest.mark.parametrize(
    ("root_state", "reserved_descendant", "expected_uncertain", "expected_hold",
     "expected_terminal"),
    (
        ("running", False, ("root",), ("leaf", "tail"), ()),
        ("running", True, ("root", "tail"), ("leaf",), ()),
        ("failed", False, (), (), ("leaf", "tail")),
    ),
)
def test_read_bridge_cannot_release_unknown_reserved_or_terminal_write(
    tmp_path, root_state, reserved_descendant,
    expected_uncertain, expected_hold, expected_terminal,
):
    journal, ledger_path, audit, registry, backend = _state(
        tmp_path,
        root_state=root_state,
        reserved_descendant=reserved_descendant,
    )
    before = journal.recover()
    result = review_synthetic_write_plan(
        journal, ledger_path, audit, registry,
    )
    assert journal.recover() == before
    assert result.uncertain_step_ids == expected_uncertain
    assert result.downstream_write_hold_step_ids == expected_hold
    assert result.terminally_blocked_write_step_ids == expected_terminal
    assert tuple(sorted(step.step_id for step in result.steps)) == (
        "independent", "leaf", "root", "tail",
    )
    assert not result.dispatch_authorized
    assert not result.automatic_replay_authorized
    assert not result.external_outcome_known
    assert backend.calls == 0
