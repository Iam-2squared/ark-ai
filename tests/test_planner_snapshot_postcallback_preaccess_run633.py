"""Deny a rebound recovery slot/hook immediately after _snapshot returns.

The snapshot callback is an untrusted synthetic seam. A forged property must
never execute between that callback and the first recovery-result field read.
All SQLite operations are fixture-only; no backend/action is dispatched.
"""

from __future__ import annotations

import pytest

from ark.agency import planner_journal_review as journal_mod
from ark.agency.contracts import PlanStep, StepState, ToolCall


def _steps() -> tuple[PlanStep, ...]:
    return (PlanStep(
        "root", ToolCall("fixture", "offline", "local", {"n": 1}),
    ),)


@pytest.mark.parametrize("action", ("recover", "append"))
@pytest.mark.parametrize(
    "member",
    (
        "tail", "step_statuses", "ambiguous_running_steps",
        "__init__", "__getattribute__", "__getattr__",
    ),
)
def test_snapshot_callback_cannot_execute_rebound_recovery_carrier(
    tmp_path, monkeypatch, action, member,
):
    journal = journal_mod.SyntheticPlanJournal(
        tmp_path / "post-snapshot-denial.sqlite", _steps(),
    )
    baseline = journal.recover()
    retained_tail = baseline.tail
    original_snapshot = journal_mod._snapshot
    receipt_type = journal_mod.SyntheticPlanRecovery
    invoked: list[str] = []

    def attack(*_args, **_kwargs):
        invoked.append(member)
        raise AssertionError("forged recovery member ran before rejection")

    with monkeypatch.context() as changes:
        def malicious_snapshot(graph, tail):
            receipt = original_snapshot(graph, tail)
            # This late mutation happens AFTER the caller's pre-snapshot
            # class custody check and BEFORE its first output field read.
            replacement = (
                property(attack) if member in (
                    "tail", "step_statuses", "ambiguous_running_steps",
                ) else attack
            )
            # __getattr__ is absent on the original slotted dataclass.
            changes.setattr(receipt_type, member, replacement, raising=False)
            return receipt

        changes.setattr(journal_mod, "_snapshot", malicious_snapshot)
        with pytest.raises(
            journal_mod.SyntheticPlanJournalRejected,
            match="synthetic recovery authority epoch changed",
        ):
            if action == "recover":
                journal.recover()
            else:
                journal.append(
                    "root", StepState.RUNNING,
                    expected_revision=0, at_ms=17, retained=retained_tail,
                )

    assert invoked == []
    # For append, refusal must occur before COMMIT; for recover, the
    # transaction is read-only. Neither path may manufacture a new event.
    restored = journal.recover()
    assert restored == baseline
    assert restored.dispatch_authorized is False
    assert restored.automatic_replay_authorized is False
