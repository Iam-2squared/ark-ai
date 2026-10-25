"""Cross-store evidence tail loss across a READ bridge never authorizes replay.

Four independently committed disposable SQLite stores are copied before
fault injection. A retained prefix witnesses both a RUNNING upstream WRITE
and a reserved downstream PENDING WRITE without invoking a real backend.
"""

import shutil
import sqlite3

import pytest

from ark.agency.audit import SQLiteActionAudit
from ark.agency.contracts import (
    Effect, OneShotAuthorization, PlanStep, ToolCall,
)
from ark.agency.durable_occurrence_review import SyntheticOccurrenceStore
from ark.agency.planner_journal_review import SyntheticPlanJournal
from ark.agency.registry import ToolRegistration, ToolRegistry
from ark.agency.synthetic_mock_action_cycle_review import (
    SyntheticMockCrashInjected, run_synthetic_mock_cycle,
)
from ark.agency.synthetic_occurrence_audit_link_review import (
    SyntheticOccurrenceAuditLinkStore,
)
from ark.agency.synthetic_write_plan_recovery_review import (
    review_synthetic_write_plan,
)


class NoDispatch:
    def __init__(self):
        self.calls = 0

    def execute(self, _call):
        self.calls += 1
        raise AssertionError("forensic review cannot dispatch an action")


def _open(root):
    root.mkdir(parents=True, exist_ok=True)
    upstream = ToolCall(
        "writer", "offline.write", "synthetic", {"step": "upstream"},
    )
    bridge = ToolCall(
        "reader", "offline.read", "synthetic", {"step": "bridge"},
    )
    downstream = ToolCall(
        "writer", "offline.write", "synthetic", {"step": "downstream"},
    )
    journal = SyntheticPlanJournal(root / "plan.sqlite", (
        PlanStep("upstream", upstream),
        PlanStep("bridge", bridge, depends_on=("upstream",)),
        PlanStep("downstream", downstream, depends_on=("bridge",)),
    ))
    ledger = SyntheticOccurrenceStore(root / "ledger.sqlite")
    audit = SQLiteActionAudit(root / "audit.sqlite", clock_ms=lambda: 15)
    links = SyntheticOccurrenceAuditLinkStore(root / "links.sqlite")
    backend = NoDispatch()
    registry = ToolRegistry((
        ToolRegistration("writer", "offline.write", Effect.WRITE, "mock", backend),
        ToolRegistration("reader", "offline.read", Effect.READ, "mock", backend),
    ))
    return journal, ledger, audit, links, registry, upstream, downstream, backend


def _review(state, **retained):
    journal, ledger, audit, links, registry, _up, _down, backend = state
    review = review_synthetic_write_plan(
        journal, ledger._path, audit, registry, link_store=links, **retained,
    )
    assert backend.calls == 0
    assert review.dispatch_authorized is False
    assert review.automatic_replay_authorized is False
    assert review.external_outcome_known is False
    return review


@pytest.mark.parametrize(("filename", "table"), (
    ("plan.sqlite", "synthetic_plan_events"),
    ("ledger.sqlite", "synthetic_occurrence_reservations"),
    ("audit.sqlite", "action_events"),
    ("links.sqlite", "synthetic_occurrence_audit_links"),
))
def test_read_bridge_and_reserved_pending_descendant_reject_four_store_loss(
    tmp_path, filename, table,
):
    original_dir = tmp_path / "source"
    state = _open(original_dir)
    journal, ledger, audit, links, registry, upstream, downstream, backend = state

    with pytest.raises(SyntheticMockCrashInjected, match="after audit link"):
        run_synthetic_mock_cycle(
            journal, ledger, audit, registry, upstream,
            OneShotAuthorization("root-token", upstream.request_id, 1000),
            step_id="upstream", occurrence_id="occ_" + "a" * 64,
            now_ms=10, fault_at="after_audit_link", link_store=links,
        )
    ledger.reserve_synthetic(
        registry, downstream,
        OneShotAuthorization("tail-token", downstream.request_id, 1000),
        occurrence_id="occ_" + "b" * 64, now_ms=12,
    )
    before = _review(state)
    assert before.uncertain_step_ids == ("downstream", "upstream")
    assert before.steps[0].step_state == "pending"
    assert before.steps[1].step_state == "running"
    assert backend.calls == 0

    first = before.steps[0]
    retained = {
        "retained_plan": first.plan_tail,
        "retained_ledger": first.ledger_witness,
        "retained_audit": first.audit_witness,
        "retained_link": first.link_witness,
    }
    assert _review(state, **retained) == before

    copied = tmp_path / "copied"
    copied.mkdir()
    for name in ("plan.sqlite", "ledger.sqlite", "audit.sqlite", "links.sqlite"):
        shutil.copy2(original_dir / name, copied / name)
    clone = _open(copied)
    assert _review(clone, **retained) == before

    # Independent history loss in just one source must not be treated as
    # successful recovery even though other retained histories still verify.
    with sqlite3.connect(copied / filename) as conn:
        n = conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
        assert n >= 1
        conn.execute(
            f"DELETE FROM {table} WHERE rowid="
            f"(SELECT MAX(rowid) FROM {table})"
        )
        assert conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0] == n - 1
    with pytest.raises(RuntimeError):
        _review(clone, **retained)
    assert clone[7].calls == 0
    assert _review(state, **retained) == before
