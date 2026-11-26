"""Planner journal pins original nested carriers across callback boundaries.

These are disconnected SQLite/recovery fixtures; a RUNNING step stays
ambiguous and is never authorized for external WRITE or automatic replay.
"""

from pathlib import Path

import pytest

import ark.agency.planner_journal_review as module
from ark.agency.contracts import PlanStep, StepState, ToolCall
from ark.agency.planner_journal_review import (
    SyntheticPlanJournal,
    SyntheticPlanJournalRejected,
)


def _fixture(tmp_path: Path):
    root = PlanStep(
        "root", ToolCall("offline", "mock", "local", {"event": "begin"}),
    )
    child = PlanStep(
        "child", ToolCall("offline", "mock", "local", {"event": "later"}),
        depends_on=("root",),
    )
    journal = SyntheticPlanJournal(tmp_path / "journal.sqlite", (root, child))
    return journal, root, child


def _equivalent_call(call: ToolCall) -> ToolCall:
    replacement = ToolCall(
        call.tool, call.capability, call.scope, dict(call.arguments),
    )
    assert replacement.request_id == call.request_id
    assert replacement is not call
    return replacement


def test_first_topology_digest_callback_cannot_rebase_step_call(
    tmp_path: Path, monkeypatch,
):
    journal, root, _child = _fixture(tmp_path)
    old_call = root.call
    original_digest = module.PlanGraph.topology_digest
    triggered = False

    def mutate_after_digest(graph):
        nonlocal triggered
        digest = original_digest(graph)
        if not triggered:
            triggered = True
            object.__setattr__(root, "call", _equivalent_call(old_call))
        return digest

    monkeypatch.setattr(module.PlanGraph, "topology_digest", mutate_after_digest)
    with pytest.raises(SyntheticPlanJournalRejected, match="topology changed"):
        journal.recover()
    assert triggered
    object.__setattr__(root, "call", old_call)
    monkeypatch.setattr(module.PlanGraph, "topology_digest", original_digest)
    assert journal.recover().tail.event_count == 0


def test_recover_rejects_equal_value_action_replacement_during_replay(
    tmp_path: Path, monkeypatch,
):
    journal, root, _child = _fixture(tmp_path)
    old_call = root.call
    original_replay = journal._replay

    def change_after_replay(conn):
        result = original_replay(conn)
        object.__setattr__(root, "call", _equivalent_call(old_call))
        return result

    monkeypatch.setattr(journal, "_replay", change_after_replay)
    with pytest.raises(SyntheticPlanJournalRejected, match="topology changed"):
        journal.recover()
    object.__setattr__(root, "call", old_call)
    monkeypatch.setattr(journal, "_replay", original_replay)
    assert journal.recover().ambiguous_running_steps == ()


def test_append_refuses_equal_value_dependency_swap_before_commit(
    tmp_path: Path, monkeypatch,
):
    journal, _root, child = _fixture(tmp_path)
    original_deps = child.depends_on
    real_snapshot = module._snapshot
    calls = 0

    def mutate_after_snapshot(graph, tail):
        nonlocal calls
        result = real_snapshot(graph, tail)
        calls += 1
        replacement = tuple(list(original_deps))
        assert replacement == original_deps
        assert replacement is not original_deps
        object.__setattr__(child, "depends_on", replacement)
        return result

    monkeypatch.setattr(module, "_snapshot", mutate_after_snapshot)
    with pytest.raises(SyntheticPlanJournalRejected, match="topology changed"):
        journal.append("root", StepState.RUNNING, expected_revision=0, at_ms=10)
    assert calls == 1
    object.__setattr__(child, "depends_on", original_deps)
    monkeypatch.setattr(module, "_snapshot", real_snapshot)
    assert journal.recover().tail.event_count == 0


def test_stable_planner_journal_still_preserves_unknown_non_replay(
    tmp_path: Path,
):
    journal, _root, _child = _fixture(tmp_path)
    initial = journal.recover()
    assert initial.tail.event_count == 0
    running = journal.append(
        "root", StepState.RUNNING, expected_revision=0, at_ms=10,
    )
    assert running.ambiguous_running_steps == ("root",)
    assert journal.recover(retained=running.tail) == running
    assert running.dispatch_authorized is False
    assert running.automatic_replay_authorized is False
