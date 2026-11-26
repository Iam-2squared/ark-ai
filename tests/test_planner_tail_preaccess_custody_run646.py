"""Retained Planner tail slots never execute replaced class descriptors.

Only isolated synthetic SQLite journal fixtures are used. Tail witnesses are
not dispatch credentials, authenticated consent, or automatic replay permits.
"""

from __future__ import annotations

import pytest

from ark.agency import planner_journal_review as journal_mod
from ark.agency.contracts import PlanStep, StepState, ToolCall


def _fixture(tmp_path):
    return journal_mod.SyntheticPlanJournal(
        tmp_path / "tail-slot-custody.sqlite",
        (PlanStep("root", ToolCall("fixture", "offline", "local", {"n": 1})),),
    )


class PoisonSlot:
    def __init__(self, calls):
        self.calls = calls

    def __get__(self, instance, owner=None):
        self.calls.append("slot")
        raise AssertionError("poison tail slot must not be invoked")


@pytest.mark.parametrize("action", ("recover", "append"))
@pytest.mark.parametrize("field", (
    "topology_digest", "event_count", "event_hash", "status_digest", "last_at_ms",
))
def test_preinstalled_tail_slot_rejected_without_open_or_poison(
    tmp_path, monkeypatch, action, field,
):
    journal = _fixture(tmp_path)
    retained = journal.recover().tail
    calls = []
    opens = []

    def forbidden_connect(*args, **kwargs):
        opens.append(True)
        raise AssertionError("SQLite access must not occur")

    with monkeypatch.context() as patch:
        patch.setattr(journal_mod.SyntheticPlanTail, field, PoisonSlot(calls))
        patch.setattr(journal_mod.sqlite3, "connect", forbidden_connect)
        with pytest.raises(
            journal_mod.SyntheticPlanJournalRejected,
            match="synthetic recovery authority epoch changed",
        ):
            if action == "recover":
                journal.recover(retained=retained)
            else:
                journal.append(
                    "root", StepState.RUNNING,
                    expected_revision=0, at_ms=1, retained=retained,
                )

    assert calls == []
    assert opens == []
    restored = journal.recover(retained=retained)
    assert restored.tail.event_count == 0
    assert restored.dispatch_authorized is False
    assert restored.automatic_replay_authorized is False


@pytest.mark.parametrize("action", ("recover", "append"))
@pytest.mark.parametrize("hook", ("__init__", "__getattribute__", "__getattr__"))
def test_preinstalled_tail_hook_rejected_without_executing_it(
    tmp_path, monkeypatch, action, hook,
):
    journal = _fixture(tmp_path)
    retained = journal.recover().tail
    calls = []

    def poison(*args, **kwargs):
        calls.append(True)
        raise AssertionError("forged tail hook must not execute")

    with monkeypatch.context() as patch:
        patch.setattr(journal_mod.SyntheticPlanTail, hook, poison, raising=False)
        with pytest.raises(
            journal_mod.SyntheticPlanJournalRejected,
            match="synthetic recovery authority epoch changed",
        ):
            if action == "recover":
                journal.recover(retained=retained)
            else:
                journal.append(
                    "root", StepState.RUNNING,
                    expected_revision=0, at_ms=1, retained=retained,
                )

    assert calls == []
    assert journal.recover(retained=retained).tail.event_count == 0


def test_unmodified_tail_stays_inert_on_restart(tmp_path):
    path = tmp_path / "tail-clean.sqlite"
    first = journal_mod.SyntheticPlanJournal(
        path,
        (PlanStep("root", ToolCall("fixture", "offline", "local", {"n": 1})),),
    )
    genesis = first.recover().tail
    first.append(
        "root", StepState.RUNNING, expected_revision=0,
        at_ms=10, retained=genesis,
    )
    restarted = journal_mod.SyntheticPlanJournal(
        path,
        (PlanStep("root", ToolCall("fixture", "offline", "local", {"n": 1})),),
    ).recover(retained=genesis)
    assert restarted.ambiguous_running_steps == ("root",)
    assert restarted.dispatch_authorized is False
    assert restarted.automatic_replay_authorized is False
