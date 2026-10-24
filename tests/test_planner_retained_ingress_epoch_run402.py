"""Retained Planner tails are held before topology and shape callbacks.

These local journal regressions do not dispatch a backend or reopen an
UNKNOWN WRITE for automatic execution.
"""

from dataclasses import replace
from pathlib import Path

import pytest

from ark.agency.contracts import PlanStep, StepState, ToolCall
from ark.agency.planner import PlanGraph
from ark.agency.planner_journal_review import (
    SyntheticPlanJournal,
    SyntheticPlanJournalRejected,
    SyntheticPlanTail,
)


def _fixture(tmp_path: Path):
    call = ToolCall("fixture", "write", "local", {"inert": True})
    journal = SyntheticPlanJournal(
        tmp_path / "plan.sqlite", (PlanStep("step", call),),
    )
    genesis = journal.recover().tail
    running = journal.append(
        "step", StepState.RUNNING, expected_revision=0, at_ms=10,
    ).tail
    return journal, genesis, running


def _retarget(retained: SyntheticPlanTail, older: SyntheticPlanTail):
    for name in (
        "topology_digest", "event_count", "event_hash",
        "status_digest", "last_at_ms",
    ):
        object.__setattr__(retained, name, getattr(older, name))


@pytest.mark.parametrize("operation", ("recover", "append"))
@pytest.mark.parametrize("callback", ("topology", "tail_shape"))
def test_original_retained_tail_cannot_rebase_to_valid_older_prefix(
    tmp_path: Path, monkeypatch, operation: str, callback: str,
):
    journal, genesis, running = _fixture(tmp_path)
    retained = replace(running)
    reflected = []

    if callback == "topology":
        original = PlanGraph.topology_digest

        def topology(self):
            digest = original(self)
            if not reflected:
                reflected.append(True)
                _retarget(retained, genesis)
            return digest

        monkeypatch.setattr(PlanGraph, "topology_digest", topology)
    else:
        original = SyntheticPlanTail.assert_shape

        def shape(self):
            if self is retained and not reflected:
                reflected.append(True)
                _retarget(retained, genesis)
            return original(self)

        monkeypatch.setattr(SyntheticPlanTail, "assert_shape", shape)

    with pytest.raises(
        SyntheticPlanJournalRejected,
        match="retained synthetic plan witness changed before",
    ):
        if operation == "recover":
            journal.recover(retained=retained)
        else:
            journal.append(
                "step", StepState.SUCCEEDED,
                expected_revision=1, at_ms=11, retained=retained,
            )
    assert reflected
    monkeypatch.undo()
    assert journal.recover().tail == running
    assert journal.recover().ambiguous_running_steps == ("step",)


def test_untampered_retained_prefix_still_allows_offline_recovery_and_append(
    tmp_path: Path,
):
    journal, _genesis, running = _fixture(tmp_path)
    replayed = journal.recover(retained=replace(running))
    assert replayed.tail == running
    assert replayed.automatic_replay_authorized is False
    finished = journal.append(
        "step", StepState.SUCCEEDED,
        expected_revision=1, at_ms=11, retained=replace(running),
    )
    assert finished.tail.event_count == 2
    assert finished.automatic_replay_authorized is False
    assert journal.recover().ambiguous_running_steps == ()
