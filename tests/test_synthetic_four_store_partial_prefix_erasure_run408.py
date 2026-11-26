"""A separately retained four-store witness catches partial row erasure.

Only temporary copies of disposable synthetic SQLite fixtures are modified.
The original histories remain intact. No real action or backend is invoked.
"""

import shutil
import sqlite3

import pytest

from ark.agency.audit import SQLiteActionAudit
from ark.agency.contracts import (
    Effect,
    OneShotAuthorization,
    PlanStep,
    ToolCall,
)
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


class NeverExecute:
    def __init__(self):
        self.calls = 0

    def execute(self, _call):
        self.calls += 1
        raise AssertionError("partial-erasure diagnosis cannot dispatch")


def _state(root):
    root.mkdir(parents=True, exist_ok=True)
    calls = (
        ToolCall("writer", "fixture.write", "offline", {"step": "one"}),
        ToolCall("writer", "fixture.write", "offline", {"step": "two"}),
    )
    journal = SyntheticPlanJournal(root / "plan.sqlite", (
        PlanStep("one", calls[0]), PlanStep("two", calls[1]),
    ))
    ledger = SyntheticOccurrenceStore(root / "occurrence.sqlite")
    audit = SQLiteActionAudit(root / "audit.sqlite", clock_ms=lambda: 15)
    links = SyntheticOccurrenceAuditLinkStore(root / "links.sqlite")
    backend = NeverExecute()
    registry = ToolRegistry((
        ToolRegistration("writer", "fixture.write", Effect.WRITE, "mock", backend),
    ))
    return journal, ledger, audit, links, registry, calls, backend


def _fault(state, index):
    journal, ledger, audit, links, registry, calls, _backend = state
    call = calls[index]
    with pytest.raises(SyntheticMockCrashInjected, match="after audit link"):
        run_synthetic_mock_cycle(
            journal, ledger, audit, registry, call,
            OneShotAuthorization(
                "token-" + str(index), call.request_id, 1000,
            ),
            step_id=("one", "two")[index],
            occurrence_id="occ_" + str(index + 1) * 64,
            now_ms=10 + index, fault_at="after_audit_link",
            link_store=links,
        )


def _review(state, **retained):
    journal, ledger, audit, links, registry, _calls, backend = state
    outcome = review_synthetic_write_plan(
        journal, ledger._path, audit, registry,
        link_store=links, **retained,
    )
    assert backend.calls == 0
    assert outcome.automatic_replay_authorized is False
    assert outcome.dispatch_authorized is False
    return outcome


@pytest.mark.parametrize(("filename", "table"), (
    ("plan.sqlite", "synthetic_plan_events"),
    ("occurrence.sqlite", "synthetic_occurrence_reservations"),
    ("audit.sqlite", "action_events"),
    ("links.sqlite", "synthetic_occurrence_audit_links"),
))
def test_one_row_erased_from_a_nonempty_four_store_history_is_rejected(
    tmp_path, filename, table,
):
    original_root = tmp_path / "original"
    original = _state(original_root)
    _fault(original, 0)
    _fault(original, 1)
    before = _review(original)
    assert before.uncertain_step_ids == ("one", "two")
    first = before.steps[0]
    retained = dict(
        retained_plan=first.plan_tail,
        retained_ledger=first.ledger_witness,
        retained_audit=first.audit_witness,
        retained_link=first.link_witness,
    )
    assert first.link_witness.event_count == 2

    # Clone all four independently committed databases. Only this expendable
    # copy is fault-injected; protected repository and original evidence stay.
    cloned_root = tmp_path / "cloned"
    cloned_root.mkdir()
    for name in ("plan.sqlite", "occurrence.sqlite", "audit.sqlite", "links.sqlite"):
        shutil.copy2(original_root / name, cloned_root / name)
    cloned = _state(cloned_root)
    assert _review(cloned, **retained) == before

    connection = sqlite3.connect(cloned_root / filename)
    try:
        connection.execute(
            f"DELETE FROM {table} "
            f"WHERE rowid=(SELECT MIN(rowid) FROM {table})"
        )
        connection.commit()
    finally:
        connection.close()

    with pytest.raises(RuntimeError):
        _review(cloned, **retained)
    assert cloned[6].calls == 0
    assert _review(original, **retained) == before
