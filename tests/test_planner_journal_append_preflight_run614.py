"""Invalid synthetic planner inputs must not open a SQLite journal.

All fixtures are local; no ToolBackend, dispatch or automatic replay.
"""

from __future__ import annotations

import pytest

from ark.agency.contracts import PlanStep, StepState, ToolCall
from ark.agency.planner_journal_review import (
    SyntheticPlanJournal,
    SyntheticPlanJournalRejected,
)


def _journal(tmp_path):
    return SyntheticPlanJournal(
        tmp_path / "isolated-plan.sqlite",
        (PlanStep("root", ToolCall("fixture", "offline", "local", {"n": 1})),),
    )


def _forbid_sqlite(_journal, monkeypatch):
    opened = []

    def forbidden(*_args, **_kwargs):
        opened.append(True)
        raise AssertionError("malformed append must not replay SQLite")

    monkeypatch.setattr(_journal, "_connect", forbidden)
    return opened


@pytest.mark.parametrize("step_id", ("", "unknown", 17, True, None, ()))
def test_bad_step_refused_before_replay(
    tmp_path, monkeypatch: pytest.MonkeyPatch, step_id,
) -> None:
    journal = _journal(tmp_path)
    with monkeypatch.context() as patch:
        opened = _forbid_sqlite(journal, patch)
        with pytest.raises(
            SyntheticPlanJournalRejected, match="invalid synthetic plan step",
        ):
            journal.append(
                step_id, StepState.RUNNING, expected_revision=0, at_ms=1,
            )
    assert opened == []
    assert journal.recover().tail.event_count == 0


@pytest.mark.parametrize("revision", (True, -1, 2**63, "0", None, 0.0))
def test_bad_revision_refused_before_replay(
    tmp_path, monkeypatch: pytest.MonkeyPatch, revision,
) -> None:
    journal = _journal(tmp_path)
    with monkeypatch.context() as patch:
        opened = _forbid_sqlite(journal, patch)
        with pytest.raises(
            SyntheticPlanJournalRejected, match="expected revision",
        ):
            journal.append(
                "root", StepState.RUNNING,
                expected_revision=revision, at_ms=1,
            )
    assert opened == []
    assert journal.recover().tail.event_count == 0


def test_legitimate_append_and_restart_remain_non_authorizing(tmp_path) -> None:
    journal = _journal(tmp_path)
    committed = journal.append(
        "root", StepState.RUNNING, expected_revision=0, at_ms=1,
    )
    observed = _journal(tmp_path).recover(retained=committed.tail)
    assert observed.tail.event_count == 1
    assert observed.ambiguous_running_steps == ("root",)
    assert observed.dispatch_authorized is False
    assert observed.automatic_replay_authorized is False
