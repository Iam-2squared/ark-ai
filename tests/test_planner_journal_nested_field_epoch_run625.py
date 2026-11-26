"""Original nested Planner identities survive digest-equal callback substitutions.

Only the disconnected SQLite journal is involved. A local synthetic RUNNING
step is not a tool dispatch or automatic retry authorization.
"""

from pathlib import Path

import pytest

import ark.agency.planner_journal_review as journal_module
from ark.agency.contracts import PlanStep, StepState, ToolCall
from ark.agency.planner_journal_review import (
    SyntheticPlanJournal,
    SyntheticPlanJournalRejected,
)


def _journal(tmp_path: Path):
    step = PlanStep(
        "step_root", ToolCall(
            "offline.worker", "mock.read", "local.scope", {"payload": 1},
        ),
    )
    return SyntheticPlanJournal(tmp_path / "journal.sqlite", (step,)), step


def _distinct_equal(value: str) -> str:
    clone = ("!" + value)[1:]
    assert clone == value and clone is not value
    return clone


@pytest.mark.parametrize("field", ("step_id", "tool", "capability", "scope"))
@pytest.mark.parametrize("operation", ("recover", "append"))
def test_digest_equal_nested_replacement_is_denied_before_recovery_or_commit(
    tmp_path: Path, monkeypatch, field: str, operation: str,
):
    journal, step = _journal(tmp_path)
    target = step if field == "step_id" else step.call
    original = getattr(target, field)
    clone = _distinct_equal(original)
    original_digest = journal_module.PlanGraph.topology_digest
    mutated = False

    def inject_after_digest(graph):
        nonlocal mutated
        digest = original_digest(graph)
        if not mutated:
            mutated = True
            object.__setattr__(target, field, clone)
        return digest

    try:
        with monkeypatch.context() as patch:
            patch.setattr(journal_module.PlanGraph, "topology_digest", inject_after_digest)
            with pytest.raises(SyntheticPlanJournalRejected, match="topology"):
                if operation == "recover":
                    journal.recover()
                else:
                    journal.append(
                        "step_root", StepState.RUNNING,
                        expected_revision=0, at_ms=10,
                    )
        assert mutated
    finally:
        object.__setattr__(target, field, original)

    unchanged = journal.recover()
    assert unchanged.tail.event_count == 0
    assert unchanged.ambiguous_running_steps == ()
    assert unchanged.dispatch_authorized is False
    assert unchanged.automatic_replay_authorized is False


@pytest.mark.parametrize("field", ("tool", "capability", "scope", "step_id"))
def test_nested_field_swap_during_snapshot_rolls_back_local_append(
    tmp_path: Path, monkeypatch, field: str,
):
    journal, step = _journal(tmp_path)
    target = step if field == "step_id" else step.call
    original = getattr(target, field)
    clone = _distinct_equal(original)
    snapshot = journal_module._snapshot
    injected = False

    def inject_after_snapshot(graph, tail):
        nonlocal injected
        result = snapshot(graph, tail)
        injected = True
        object.__setattr__(target, field, clone)
        return result

    try:
        with monkeypatch.context() as patch:
            patch.setattr(journal_module, "_snapshot", inject_after_snapshot)
            with pytest.raises(SyntheticPlanJournalRejected, match="topology"):
                journal.append(
                    "step_root", StepState.RUNNING,
                    expected_revision=0, at_ms=10,
                )
        assert injected
    finally:
        object.__setattr__(target, field, original)

    restored = journal.recover()
    assert restored.tail.event_count == 0
    assert restored.automatic_replay_authorized is False
