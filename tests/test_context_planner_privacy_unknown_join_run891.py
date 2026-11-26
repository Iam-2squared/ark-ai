"""Cold Planner ambiguity and privacy revocation jointly deny context use.

Combines independent disposable local SQLite stores. Neither an intact Memory
record nor an unknown running plan is consent, retry permission or dispatch.
"""

import pytest

from ark.agency.contracts import PlanStep, StepState, ToolCall
from ark.agency.planner_journal_review import SyntheticPlanJournal
from ark.memory import MemoryScope, MemoryWrite, SQLiteMemoryStore
from ark.memory.coherent_snapshot_review import CoherentSnapshotRequest
from ark.personal_context_review import ContextSelectionPolicy
from ark.personal_context_revocation_review import (
    SyntheticContextRevocationLedger,
    SyntheticContextRevocationRejected,
    review_fresh_nonrevoked_context,
)


def _fixtures(tmp_path):
    store = SQLiteMemoryStore(tmp_path / "memory.sqlite", clock_ms=lambda: 100)
    private = MemoryScope("synthetic-owner", "private")
    notes = MemoryScope("synthetic-owner", "notes")
    store.put(MemoryWrite(private, "private-source", "private synthetic text"))
    store.put(MemoryWrite(notes, "notes-source", "safe synthetic notes"))
    ledger = SyntheticContextRevocationLedger(tmp_path / "veto.sqlite")
    step = PlanStep(
        "context-review", ToolCall(
            "offline.inspect", "fixture.read", "synthetic", {},
        ),
    )
    journal_path = tmp_path / "plan.sqlite"
    journal = SyntheticPlanJournal(journal_path, (step,))
    running = journal.append(
        "context-review", StepState.RUNNING, expected_revision=0, at_ms=90,
    )
    return store, private, notes, ledger, journal_path, step, running.tail


def test_revocation_blocks_context_even_with_durable_running_plan(tmp_path):
    store, private, _notes, ledger, plan_path, step, tail = _fixtures(tmp_path)
    ledger.revoke(private, at_ms=100)
    recovered = SyntheticPlanJournal(plan_path, (step,)).recover()
    assert recovered.tail == tail
    assert recovered.ambiguous_running_steps == ("context-review",)
    assert recovered.dispatch_authorized is False
    assert recovered.automatic_replay_authorized is False
    with pytest.raises(SyntheticContextRevocationRejected, match="revoked"):
        review_fresh_nonrevoked_context(
            store, CoherentSnapshotRequest("synthetic-owner", ("private",)),
            ContextSelectionPolicy(4, 4), ledger,
        )
    assert SyntheticPlanJournal(plan_path, (step,)).recover().tail == tail


def test_unrelated_context_is_read_only_while_private_scope_is_revoked(tmp_path):
    store, private, notes, ledger, plan_path, step, tail = _fixtures(tmp_path)
    ledger.revoke(private, at_ms=100)
    selected = review_fresh_nonrevoked_context(
        store, CoherentSnapshotRequest("synthetic-owner", (notes.namespace,)),
        ContextSelectionPolicy(4, 4), ledger,
    )
    assert len(selected.items) == 1
    assert selected.items[0].content == "safe synthetic notes"
    assert selected.action_authorized is False
    assert selected.dispatch_authorized is False
    with pytest.raises(SyntheticContextRevocationRejected, match="revoked"):
        review_fresh_nonrevoked_context(
            store,
            CoherentSnapshotRequest("synthetic-owner", (notes.namespace, private.namespace)),
            ContextSelectionPolicy(4, 4), ledger,
        )
    assert SyntheticPlanJournal(plan_path, (step,)).recover().tail == tail
