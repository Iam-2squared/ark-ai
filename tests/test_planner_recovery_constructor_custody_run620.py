"""Synthetic Planner recovery constructor identity is fixed before SQLite.

Only disposable offline fixture events are used; none authorizes replay,
backend dispatch, a human decision, or a physical-world effect.
"""

import pytest

from ark.agency import planner_journal_review as journal_mod
from ark.agency.contracts import PlanStep, StepState, ToolCall


def _journal(tmp_path):
    steps = (PlanStep("root", ToolCall("fixture", "read.mock", "local")),)
    return journal_mod.SyntheticPlanJournal(tmp_path / "plan.sqlite", steps)


def _operation(journal, operation):
    if operation == "recover":
        return journal.recover()
    return journal.append("root", StepState.RUNNING, expected_revision=0, at_ms=7)


@pytest.mark.parametrize("operation", ("recover", "append"))
def test_preinstalled_forged_recovery_constructor_denied_before_sqlite(
    tmp_path, monkeypatch, operation,
):
    journal = _journal(tmp_path)
    forged_calls = []

    def forbidden(*_args, **_kwargs):
        forged_calls.append("invoked")
        raise AssertionError("forged constructor must not run")

    def forbidden_sqlite(*_args, **_kwargs):
        raise AssertionError("SQLite must not open for a forged recovery constructor")

    with monkeypatch.context() as patch:
        patch.setattr(journal_mod.SyntheticPlanRecovery, "__init__", forbidden)
        patch.setattr(journal_mod.sqlite3, "connect", forbidden_sqlite)
        with pytest.raises(
            journal_mod.SyntheticPlanJournalRejected,
            match="synthetic recovery authority epoch changed",
        ):
            _operation(journal, operation)

    assert forged_calls == []
    assert journal.recover().tail.event_count == 0


@pytest.mark.parametrize("operation", ("recover", "append"))
def test_snapshot_rebinding_constructor_fails_before_publish(
    tmp_path, monkeypatch, operation,
):
    journal = _journal(tmp_path)
    actual_snapshot = journal_mod._snapshot
    forged_calls = []

    def forbidden(*_args, **_kwargs):
        forged_calls.append("invoked")
        raise AssertionError("forged recovery constructor must not run")

    with monkeypatch.context() as patch:
        def swap_after_valid_snapshot(graph, tail):
            result = actual_snapshot(graph, tail)
            patch.setattr(journal_mod.SyntheticPlanRecovery, "__init__", forbidden)
            return result

        patch.setattr(journal_mod, "_snapshot", swap_after_valid_snapshot)
        with pytest.raises(
            journal_mod.SyntheticPlanJournalRejected,
            match="synthetic recovery authority epoch changed",
        ):
            _operation(journal, operation)

    assert forged_calls == []
    # The append transaction was not committed; recover is read-only.
    assert journal.recover().tail.event_count == 0


def test_unmodified_running_recovery_stays_manual_only(tmp_path):
    journal = _journal(tmp_path)
    committed = journal.append("root", StepState.RUNNING, expected_revision=0, at_ms=7)
    restarted = journal.recover(retained=committed.tail)
    assert restarted.tail.event_count == 1
    assert restarted.ambiguous_running_steps == ("root",)
    assert restarted.dispatch_authorized is False
    assert restarted.automatic_replay_authorized is False
