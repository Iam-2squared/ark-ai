"""Four-store tail-loss recovery regression; disconnected SQLite only.

A caller-retained witness is stored independently from the four SQLite files.
Deleting their last committed rows must never upgrade reserved/RUNNING WRITE
to safe replay, even if earlier prefixes still look structurally valid.
"""

import shutil
import sqlite3

import pytest

from ark.agency.audit import SQLiteActionAudit
from ark.agency.contracts import Effect, OneShotAuthorization, PlanStep, ToolCall
from ark.agency.durable_occurrence_review import SyntheticOccurrenceStore
from ark.agency.planner_journal_review import SyntheticPlanJournal
from ark.agency.registry import ToolRegistration, ToolRegistry
from ark.agency.synthetic_mock_action_cycle_review import (
    SyntheticMockCrashInjected,
    run_synthetic_mock_cycle,
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
        raise AssertionError("recovery diagnosis must never dispatch")


def _open(root):
    root.mkdir(parents=True, exist_ok=True)
    calls = (
        ToolCall("writer", "offline.write", "synthetic", {"index": 1}),
        ToolCall("writer", "offline.write", "synthetic", {"index": 2}),
    )
    plan = SyntheticPlanJournal(root / "plan.sqlite", (
        PlanStep("first", calls[0]), PlanStep("second", calls[1]),
    ))
    ledger = SyntheticOccurrenceStore(root / "ledger.sqlite")
    audit = SQLiteActionAudit(root / "audit.sqlite", clock_ms=lambda: 15)
    links = SyntheticOccurrenceAuditLinkStore(root / "links.sqlite")
    backend = NoDispatch()
    registry = ToolRegistry((
        ToolRegistration("writer", "offline.write", Effect.WRITE, "mock", backend),
    ))
    return plan, ledger, audit, links, registry, calls, backend


def _two_linked_crash_prefixes(state):
    plan, ledger, audit, links, registry, calls, _backend = state
    for idx, call in enumerate(calls):
        with pytest.raises(SyntheticMockCrashInjected, match="after audit link"):
            run_synthetic_mock_cycle(
                plan, ledger, audit, registry, call,
                OneShotAuthorization(
                    f"synthetic-token-{idx}", call.request_id, 1000,
                ),
                step_id=("first", "second")[idx],
                occurrence_id="occ_" + str(idx + 1) * 64,
                now_ms=10 + idx,
                fault_at="after_audit_link", link_store=links,
            )


def _review(state, **retained):
    plan, ledger, audit, links, registry, _calls, backend = state
    result = review_synthetic_write_plan(
        plan, ledger._path, audit, registry, link_store=links, **retained,
    )
    assert backend.calls == 0
    assert result.dispatch_authorized is False
    assert result.automatic_replay_authorized is False
    assert result.external_outcome_known is False
    return result


@pytest.mark.parametrize(("file", "table"), (
    ("plan.sqlite", "synthetic_plan_events"),
    ("ledger.sqlite", "synthetic_occurrence_reservations"),
    ("audit.sqlite", "action_events"),
    ("links.sqlite", "synthetic_occurrence_audit_links"),
))
def test_last_committed_row_loss_is_denied_with_retained_four_store_proof(
    tmp_path, file, table,
):
    original_dir = tmp_path / "original"
    original = _open(original_dir)
    _two_linked_crash_prefixes(original)
    prior = _review(original)
    assert prior.uncertain_step_ids == ("first", "second")
    first = prior.steps[0]
    retained = {
        "retained_plan": first.plan_tail,
        "retained_ledger": first.ledger_witness,
        "retained_audit": first.audit_witness,
        "retained_link": first.link_witness,
    }
    assert first.link_witness.event_count == 2

    cloned_dir = tmp_path / "clone"
    cloned_dir.mkdir()
    for name in ("plan.sqlite", "ledger.sqlite", "audit.sqlite", "links.sqlite"):
        shutil.copy2(original_dir / name, cloned_dir / name)
    cloned = _open(cloned_dir)
    assert _review(cloned, **retained) == prior

    # The previous first entry survives. Only the most recent history entry
    # is removed from one disposable store, then all four are independently
    # reviewed with retained evidence.
    with sqlite3.connect(cloned_dir / file) as conn:
        assert conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0] == 2
        conn.execute(
            f"DELETE FROM {table} "
            f"WHERE rowid=(SELECT MAX(rowid) FROM {table})"
        )
        assert conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0] == 1
    with pytest.raises(RuntimeError):
        _review(cloned, **retained)
    assert cloned[6].calls == 0
    assert _review(original, **retained) == prior
