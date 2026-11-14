"""Disconnected Planner journal must not be retargeted before restart.

This is strictly local replay/append safety; no action executor is connected.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from ark.agency.contracts import PlanStep, StepState, ToolCall
from ark.agency.planner_journal_review import (
    SyntheticPlanJournal,
    SyntheticPlanJournalRejected,
)


def _steps():
    return (
        PlanStep("root", ToolCall("fixture", "offline", "local", {"n": 1})),
        PlanStep(
            "child", ToolCall("fixture", "offline", "local", {"n": 2}),
            ("root",),
        ),
    )


def test_path_subclass_cannot_open_journal_or_run_custom_fspath(tmp_path):
    touched = []

    class UntrustedPath(type(Path())):
        def __fspath__(self):
            touched.append(True)
            return str(tmp_path / "redirect.sqlite")

    with pytest.raises(TypeError, match="exact pathlib.Path"):
        SyntheticPlanJournal(
            UntrustedPath(tmp_path / "source.sqlite"), _steps(),
        )
    assert touched == []
    assert not (tmp_path / "redirect.sqlite").exists()
    assert not (tmp_path / "source.sqlite").exists()


@pytest.mark.parametrize("action", ("recover", "append"))
@pytest.mark.parametrize("replacement", ("different", "equal_carrier"))
def test_retargeted_path_rejected_before_open(tmp_path, action, replacement):
    source = tmp_path / "source.sqlite"
    journal = SyntheticPlanJournal(source, _steps())
    original = journal.recover()
    other = (
        tmp_path / "different.sqlite"
        if replacement == "different"
        else Path(str(source))
    )
    assert other is not source
    if replacement == "equal_carrier":
        assert other == source

    journal._path = other
    with pytest.raises(
        SyntheticPlanJournalRejected, match="source identity changed",
    ):
        if action == "recover":
            journal.recover()
        else:
            journal.append(
                "root", StepState.RUNNING,
                expected_revision=0, at_ms=10,
            )

    assert not (tmp_path / "different.sqlite").exists()
    assert SyntheticPlanJournal(source, _steps()).recover() == original


def test_untouched_source_supports_failed_blocked_replay_after_restart(tmp_path):
    source = tmp_path / "source.sqlite"
    journal = SyntheticPlanJournal(source, _steps())
    first = journal.append(
        "root", StepState.RUNNING, expected_revision=0, at_ms=1,
    )
    assert first.ambiguous_running_steps == ("root",)
    terminal = journal.append(
        "root", StepState.FAILED, expected_revision=1, at_ms=2,
    )
    recovered = SyntheticPlanJournal(source, _steps()).recover(retained=first.tail)
    assert recovered == terminal
    assert recovered.step_statuses == (
        ("child", "blocked", 1), ("root", "failed", 2),
    )
    assert recovered.dispatch_authorized is False
    assert recovered.automatic_replay_authorized is False
