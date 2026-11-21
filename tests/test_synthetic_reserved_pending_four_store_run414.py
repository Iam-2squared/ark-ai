"""A reserved-PENDING root plus independent RUNNING WRITE survives partial erasure.

Four separately committed disposable SQLite files; this is local diagnostic
evidence only and never makes a pending reservation safe to execute/replay.
"""

import shutil
import sqlite3

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
from ark.agency.synthetic_occurrence_audit_link_review import (
    SyntheticOccurrenceAuditLinkStore,
)
from ark.agency.synthetic_write_plan_recovery_review import (
    review_synthetic_write_plan,
)


class NeverExecute:
    def __init__(self):
        self.calls = 0

    def execute(self, _call):
        self.calls += 1
        raise AssertionError("disconnected diagnosis must not execute tools")


def _state(root):
    root.mkdir(parents=True, exist_ok=True)
    root_call = ToolCall("writer", "write", "offline", {"step": "root"})
    later_call = ToolCall("writer", "write", "offline", {"step": "dependent"})
    free_call = ToolCall("writer", "write", "offline", {"step": "independent"})
    read_call = ToolCall("reader", "read", "offline")
    journal = SyntheticPlanJournal(root / "plan.sqlite", (
        PlanStep("root", root_call),
        PlanStep("bridge", read_call, ("root",)),
        PlanStep("dependent", later_call, ("bridge",)),
        PlanStep("independent", free_call),
    ))
    ledger = SyntheticOccurrenceStore(root / "occurrence.sqlite")
    audit = SQLiteActionAudit(root / "audit.sqlite", clock_ms=lambda: 12)
    links = SyntheticOccurrenceAuditLinkStore(root / "links.sqlite")
    backend = NeverExecute()
    registry = ToolRegistry((
        ToolRegistration("writer", "write", Effect.WRITE, "mock", backend),
        ToolRegistration("reader", "read", Effect.READ, "mock", backend),
    ))
    return journal, ledger, audit, links, registry, root_call, backend


def _build_crash_prefix(state):
    journal, ledger, audit, links, registry, call, _backend = state
    # A reservation may be committed despite the Planner still saying PENDING.
    receipt = ledger.reserve_synthetic(
        registry, call,
        OneShotAuthorization("root-only", call.request_id, 1000),
        occurrence_id="occ_" + "a" * 64, now_ms=10,
    )
    event = audit.append(call, outcome="synthetic_audit_before_mock")
    links.link_synthetic(
        registry, call, ledger, receipt, audit, event, at_ms=15,
    )
    # Independent locally RUNNING never resolves or unlocks the root.
    journal.append("independent", StepState.RUNNING, expected_revision=0, at_ms=16)


def _review(state, **retained):
    journal, ledger, audit, links, registry, _call, backend = state
    result = review_synthetic_write_plan(
        journal, ledger._path, audit, registry, link_store=links, **retained,
    )
    assert backend.calls == 0
    assert result.dispatch_authorized is False
    assert result.automatic_replay_authorized is False
    assert result.external_outcome_known is False
    return result


@pytest.mark.parametrize(("filename", "table"), (
    ("plan.sqlite", "synthetic_plan_events"),
    ("occurrence.sqlite", "synthetic_occurrence_reservations"),
    ("audit.sqlite", "action_events"),
    ("links.sqlite", "synthetic_occurrence_audit_links"),
))
def test_retained_reserved_pending_rejects_each_single_store_erasure(
    tmp_path, filename, table,
):
    source = _state(tmp_path / "original")
    _build_crash_prefix(source)
    before = _review(source)
    assert before.uncertain_step_ids == ("independent", "root")
    assert before.downstream_write_hold_step_ids == ("dependent",)
    assert before.terminally_blocked_write_step_ids == ()
    assert source[0].recover().ambiguous_running_steps == ("independent",)
    prefix = before.steps[0]
    retained = dict(
        retained_plan=prefix.plan_tail,
        retained_ledger=prefix.ledger_witness,
        retained_audit=prefix.audit_witness,
        retained_link=prefix.link_witness,
    )
    assert prefix.link_witness.event_count == 1

    dest = tmp_path / "clone"
    dest.mkdir()
    for name in ("plan.sqlite", "occurrence.sqlite", "audit.sqlite", "links.sqlite"):
        shutil.copy2(tmp_path / "original" / name, dest / name)
    reopened = _state(dest)
    assert _review(reopened, **retained) == before

    with sqlite3.connect(dest / filename) as conn:
        conn.execute(
            f"DELETE FROM {table} WHERE rowid=(SELECT MIN(rowid) FROM {table})"
        )
    with pytest.raises(RuntimeError):
        _review(reopened, **retained)
    assert reopened[6].calls == 0
    assert _review(source, **retained) == before
