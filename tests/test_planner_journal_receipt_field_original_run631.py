"""Recovery-only Planner journal receipts refuse executable class shims.

All transitions are synthetic local SQLite fixtures. No external tool or
replay is authorized, even if a result's false-only properties are intact.
"""

import pytest

from ark.agency import planner_journal_review as journal_mod
from ark.agency.contracts import PlanStep, StepState, ToolCall


def _journal(tmp_path):
    return journal_mod.SyntheticPlanJournal(
        tmp_path / "recovery-carriers.sqlite",
        (PlanStep("root", ToolCall("fixture", "offline", "local", {"n": 1})),),
    )


class ExecutableSlot:
    def __init__(self, invoked):
        self.invoked = invoked

    def __get__(self, instance, owner=None):
        self.invoked.append(True)
        raise AssertionError("forged receipt slot must never execute")


@pytest.mark.parametrize("field", journal_mod._RECOVERY_FIELDS)
@pytest.mark.parametrize("action", ("recover", "append"))
def test_preinstalled_result_slot_denied_before_sqlite(
    tmp_path, monkeypatch, field, action,
):
    journal = _journal(tmp_path)
    invoked = []
    opens = []

    def forbidden(*args, **kwargs):
        opens.append(True)
        raise AssertionError("forged receipt must not open SQLite")

    with monkeypatch.context() as patch:
        patch.setattr(
            journal_mod.SyntheticPlanRecovery, field,
            ExecutableSlot(invoked),
        )
        patch.setattr(journal_mod.sqlite3, "connect", forbidden)
        with pytest.raises(
            journal_mod.SyntheticPlanJournalRejected,
            match="synthetic recovery authority epoch changed",
        ):
            if action == "recover":
                journal.recover()
            else:
                journal.append(
                    "root", StepState.RUNNING, expected_revision=0, at_ms=1,
                )
    assert invoked == []
    assert opens == []
    assert journal.recover().tail.event_count == 0


@pytest.mark.parametrize("name", ("__init__", "__getattribute__", "__getattr__"))
def test_preinstalled_recovery_hook_denied_before_invocation(
    tmp_path, monkeypatch, name,
):
    journal = _journal(tmp_path)
    calls = []

    def forbidden(*args, **kwargs):
        calls.append(True)
        raise AssertionError("forged recovery hook must never execute")

    with monkeypatch.context() as patch:
        patch.setattr(journal_mod.SyntheticPlanRecovery, name, forbidden,
                      raising=False)
        with pytest.raises(
            journal_mod.SyntheticPlanJournalRejected,
            match="synthetic recovery authority epoch changed",
        ):
            journal.recover()
    assert calls == []


def test_unmodified_recovery_keeps_crash_unknown_without_replay(tmp_path):
    journal = _journal(tmp_path)
    journal.append("root", StepState.RUNNING, expected_revision=0, at_ms=1)
    result = journal.recover()
    assert result.ambiguous_running_steps == ("root",)
    assert result.dispatch_authorized is False
    assert result.automatic_replay_authorized is False
