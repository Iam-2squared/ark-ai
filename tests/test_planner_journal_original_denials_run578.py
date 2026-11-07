"""Synthetic Planner recovery cannot gain dispatch or replay authority.

The journal remains a disconnected SQLite fixture. These cases do not
authorize any ToolBackend operation, replay or physical-world effect.
"""

from __future__ import annotations

import pytest

from ark.agency import planner_journal_review as journal_mod
from ark.agency.contracts import PlanStep, StepState, ToolCall


def _steps():
    return (PlanStep("root", ToolCall("fixture", "offline", "local", {"n": 1})),)


@pytest.mark.parametrize(
    "flag", ("dispatch_authorized", "automatic_replay_authorized"),
)
@pytest.mark.parametrize("action", ("recover", "append"))
def test_preinstalled_false_only_denial_rejected_before_sqlite(
    tmp_path, monkeypatch, flag, action,
):
    journal = journal_mod.SyntheticPlanJournal(
        tmp_path / "recovery-denials.sqlite", _steps(),
    )
    opens = []

    def forbidden(*args, **kwargs):
        opens.append((args, kwargs))
        raise AssertionError("SQLite must not open with replaced denial")

    with monkeypatch.context() as changes:
        changes.setattr(
            journal_mod.SyntheticPlanRecovery, flag,
            property(lambda _self: False),
        )
        changes.setattr(journal_mod.sqlite3, "connect", forbidden)
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
                )

    assert opens == []
    assert journal.recover().step_statuses == (("root", "pending", 0),)


@pytest.mark.parametrize("action", ("recover", "append"))
def test_reentrant_snapshot_replacement_refused_without_new_event(
    tmp_path, monkeypatch, action,
):
    journal = journal_mod.SyntheticPlanJournal(
        tmp_path / "reentrant-denials.sqlite", _steps(),
    )
    before = journal.recover()
    original = journal_mod._snapshot

    def changed_snapshot(graph, tail):
        result = original(graph, tail)
        changes.setattr(
            journal_mod.SyntheticPlanRecovery,
            "automatic_replay_authorized", property(lambda _self: False),
        )
        return result

    with monkeypatch.context() as changes:
        changes.setattr(journal_mod, "_snapshot", changed_snapshot)
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
                )

    assert journal.recover() == before


def test_unmodified_failed_terminal_can_recover_without_authority(tmp_path):
    path = tmp_path / "failed-recovery.sqlite"
    journal = journal_mod.SyntheticPlanJournal(path, _steps())
    journal.append("root", StepState.RUNNING, expected_revision=0, at_ms=1)
    journal.append("root", StepState.FAILED, expected_revision=1, at_ms=2)
    restarted = journal_mod.SyntheticPlanJournal(path, _steps()).recover()
    assert restarted.step_statuses == (("root", "failed", 2),)
    assert restarted.ambiguous_running_steps == ()
    assert restarted.dispatch_authorized is False
    assert restarted.automatic_replay_authorized is False
