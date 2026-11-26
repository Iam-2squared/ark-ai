"""Plan-wide READ-ONLY reconciliation after genuine mock-cycle process exits.

Each of the four SQLite stores commits independently. A matching local
witness is NEVER an external side-effect receipt, permission, or global
atomic transaction. No ToolBackend is invoked at any phase.
"""

from __future__ import annotations

import hashlib
import os
from multiprocessing import get_context
from pathlib import Path

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
from ark.agency.synthetic_mock_action_cycle_review import run_synthetic_mock_cycle
from ark.agency.synthetic_occurrence_audit_link_review import (
    SyntheticOccurrenceAuditLinkStore,
)
from ark.agency.synthetic_write_plan_recovery_review import (
    review_synthetic_write_plan,
)


class _ForbiddenBackend:
    def __init__(self):
        self.calls = 0

    def execute(self, _call):
        self.calls += 1
        raise AssertionError("disconnected recovery must never dispatch")


def _state(root: Path):
    root.mkdir(parents=True, exist_ok=True)
    root_call = ToolCall("fixture.writer", "mock.write", "private", {"step": "root"})
    next_call = ToolCall(
        "fixture.writer", "mock.write", "private", {"step": "dependent"},
    )
    backend = _ForbiddenBackend()
    registry = ToolRegistry((
        ToolRegistration(
            "fixture.writer", "mock.write", Effect.WRITE, "inert", backend,
        ),
    ))
    journal = SyntheticPlanJournal(
        root / "plan.sqlite",
        (
            PlanStep("root", root_call),
            PlanStep("dependent", next_call, ("root",)),
        ),
    )
    ledger = SyntheticOccurrenceStore(root / "reservations.sqlite")
    audit = SQLiteActionAudit(root / "audit.sqlite", clock_ms=lambda: 15)
    links = SyntheticOccurrenceAuditLinkStore(root / "links.sqlite")
    return root_call, backend, registry, journal, ledger, audit, links


def _child_commit_then_exit(root: str, boundary: str) -> None:
    call, _backend, registry, journal, ledger, audit, links = _state(Path(root))
    target, name = {
        "running": (journal, "append"),
        "reservation": (ledger, "reserve_synthetic"),
        "audit": (audit, "append"),
        "link": (links, "link_synthetic"),
        "terminal": (journal, "append"),
    }[boundary]
    original = getattr(target, name)

    def crash_after_commit(*args, **kwargs):
        receipt = original(*args, **kwargs)
        if boundary == "terminal" and args[1] is not StepState.SUCCEEDED:
            return receipt
        os._exit(0)  # No committed receipt reaches the caller.

    setattr(target, name, crash_after_commit)
    run_synthetic_mock_cycle(
        journal, ledger, audit, registry, call,
        OneShotAuthorization("never-approval", call.request_id, 1000),
        step_id="root",
        occurrence_id="occ_" + hashlib.sha256(b"plan-root").hexdigest(),
        now_ms=10,
        link_store=links,
    )
    os._exit(93)  # Normal completion is not an injected crash.


@pytest.mark.parametrize(
    ("boundary", "counts", "root_state"),
    (
        ("running", (0, 0, 0), "running"),
        ("reservation", (1, 0, 0), "running"),
        ("audit", (1, 1, 0), "running"),
        ("link", (1, 1, 1), "running"),
        ("terminal", (1, 1, 1), "succeeded"),
    ),
)
def test_plan_wide_cold_reconciliation_cannot_promote_crash_to_permission(
    tmp_path, boundary, counts, root_state,
):
    _state(tmp_path)
    worker = get_context("spawn").Process(
        target=_child_commit_then_exit, args=(str(tmp_path), boundary),
    )
    worker.start()
    worker.join(timeout=35)
    if worker.is_alive():
        worker.terminate()
        worker.join(timeout=5)
    assert worker.exitcode == 0

    _call, backend, registry, journal, ledger, audit, links = _state(tmp_path)
    baseline = journal.recover()
    before = (
        ledger.count_synthetic(), len(audit.events()),
        links.read_witness().event_count,
    )
    assert before == counts
    assert dict(
        (step_id, status) for step_id, status, _rev
        in baseline.step_statuses
    )["root"] == root_state

    reviewed = review_synthetic_write_plan(
        journal, ledger._path, audit, registry, link_store=links,
    )
    assert reviewed.uncertain_step_ids == ("root",)
    assert tuple(step.step_id for step in reviewed.steps) == (
        "dependent", "root",
    )
    if root_state == "running":
        assert reviewed.downstream_write_hold_step_ids == ("dependent",)
    assert reviewed.dispatch_authorized is False
    assert reviewed.automatic_replay_authorized is False
    assert reviewed.external_outcome_known is False
    assert backend.calls == 0
    assert journal.recover() == baseline
    assert (
        ledger.count_synthetic(), len(audit.events()),
        links.read_witness().event_count,
    ) == before
