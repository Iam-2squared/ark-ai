"""Synthetic Planner journal rejects value-equal retained-tail carrier swaps.

Local SQLite fixture only: no planner execution, dispatch or replay authority.
"""

from __future__ import annotations

import pytest

from ark.agency import planner_journal_review as journal_mod
from ark.agency.contracts import PlanStep, StepState, ToolCall


def _steps():
    return (PlanStep("root", ToolCall("fixture", "offline", "local", {"n": 1})),)


def _swap_equal_hash(retained):
    original = retained.event_hash
    changed = original.encode("ascii").decode("ascii")
    assert changed == original
    assert changed is not original
    object.__setattr__(retained, "event_hash", changed)


@pytest.mark.parametrize("operation", ("recover", "append"))
@pytest.mark.parametrize("boundary", ("topology", "snapshot"))
def test_equal_hash_carrier_replacement_denied_before_local_commit(
    tmp_path, monkeypatch, operation, boundary,
):
    journal = journal_mod.SyntheticPlanJournal(
        tmp_path / "retained-epoch.sqlite", _steps(),
    )
    before = journal.recover()
    retained = before.tail
    if boundary == "topology":
        original = journal._pin_topology

        def changed_topology():
            result = original()
            _swap_equal_hash(retained)
            return result

        monkeypatch.setattr(journal, "_pin_topology", changed_topology)
    else:
        original = journal_mod._snapshot

        def changed_snapshot(graph, tail):
            result = original(graph, tail)
            _swap_equal_hash(retained)
            return result

        monkeypatch.setattr(journal_mod, "_snapshot", changed_snapshot)

    with pytest.raises(
        journal_mod.SyntheticPlanJournalRejected,
        match="retained synthetic plan witness changed",
    ):
        if operation == "recover":
            journal.recover(retained=retained)
        else:
            journal.append(
                "root", StepState.RUNNING,
                expected_revision=0, at_ms=1, retained=retained,
            )

    # Only the caller-owned witness changed; the journal's own prior
    # checkpoint remains unchanged and cannot cause a hidden retry.
    monkeypatch.undo()
    assert journal.recover() == before


def test_intact_retained_genesis_supports_local_failed_recovery(tmp_path):
    path = tmp_path / "retained-good.sqlite"
    journal = journal_mod.SyntheticPlanJournal(path, _steps())
    genesis = journal.recover().tail
    running = journal.append(
        "root", StepState.RUNNING, expected_revision=0,
        at_ms=1, retained=genesis,
    )
    failed = journal.append(
        "root", StepState.FAILED, expected_revision=1,
        at_ms=2, retained=running.tail,
    )
    restarted = journal_mod.SyntheticPlanJournal(path, _steps())
    assert restarted.recover(retained=genesis) == failed
    assert restarted.recover().automatic_replay_authorized is False
