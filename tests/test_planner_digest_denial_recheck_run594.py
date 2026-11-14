"""Planner recovery must revalidate original denials after status hashing.

All callbacks here are disconnected fixtures. No ToolBackend is invoked.
"""

from __future__ import annotations

import pytest

from ark.agency import planner_journal_review as journal_mod
from ark.agency.contracts import PlanStep, StepState, ToolCall
from ark.agency.planner import PlanGraph


def _steps():
    return (PlanStep("root", ToolCall("fixture", "offline", "local", {"n": 1})),)


@pytest.mark.parametrize("action", ("recover", "append"))
def test_status_digest_cannot_rebind_false_denial_after_last_getter(
    tmp_path, monkeypatch, action,
):
    journal = journal_mod.SyntheticPlanJournal(
        tmp_path / "replay-denial-epoch.sqlite", _steps(),
    )
    baseline = journal.recover()
    # Capture caller-owned fixture input BEFORE substituting the result lookup hook.
    retained_tail = baseline.tail
    receipt_type = journal_mod.SyntheticPlanRecovery
    original_getattribute = receipt_type.__getattribute__
    original_digest = PlanGraph.status_digest
    last_getter_seen = []
    traced_calls = []
    substitutions = []

    def traced_getattribute(self, name):
        traced_calls.append(name)
        result = original_getattribute(self, name)
        if name == "automatic_replay_authorized":
            last_getter_seen.append(name)
        return result

    with monkeypatch.context() as changes:
        changes.setattr(receipt_type, "__getattribute__", traced_getattribute)

        def rebind_on_digest(self):
            if last_getter_seen and not substitutions:
                substitutions.append("dispatch_authorized")
                changes.setattr(
                    receipt_type, "dispatch_authorized", property(lambda _: False),
                )
            return original_digest(self)

        changes.setattr(PlanGraph, "status_digest", rebind_on_digest)
        with pytest.raises(
            journal_mod.SyntheticPlanJournalRejected,
            match="synthetic recovery authority epoch changed",
        ):
            if action == "recover":
                journal.recover()
            else:
                journal.append(
                    "root", StepState.RUNNING,
                    expected_revision=0, at_ms=1,
                    retained=retained_tail,
                )

    # Import-original descriptor custody now denies the forged attribute
    # lookup hook before it runs, before the chained digest callback can
    # install any false-looking authority descriptor, and before COMMIT.
    assert traced_calls == []
    assert last_getter_seen == []
    assert substitutions == []
    # Rejection occurred before COMMIT in append, so the tentative event
    # must not appear in the persistent replay-only journal.
    restored = journal.recover()
    assert restored == baseline
    assert restored.dispatch_authorized is False
    assert restored.automatic_replay_authorized is False
