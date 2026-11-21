"""Synthetic Planner journal pre-SQLite identity admission and cold restart.

Only a disposable PlanGraph with inert READ calls is used. A matching journal
tail does not authorize dispatch, COMMIT-UNKNOWN replay or a real ToolBackend.
"""

import pytest

from ark.agency.contracts import PlanStep, StepState, ToolCall
from ark.agency.planner_journal_review import (
    SyntheticPlanJournal,
    SyntheticPlanJournalRejected,
)


def _fixture(tmp_path):
    steps = (
        PlanStep(
            "root",
            ToolCall("fixture.inspect", "fixture.read", "synthetic", {"fixture": 1}),
        ),
    )
    path = tmp_path / "plan.sqlite"
    return SyntheticPlanJournal(path, steps), path, steps


class _ForbiddenSteps:
    def __iter__(self):
        raise AssertionError("invalid step ID iterated the retained plan")


class _ForbiddenHash:
    def __hash__(self):
        raise AssertionError("invalid step ID entered hash lookup")


@pytest.mark.parametrize(
    "bad",
    ("a" * 4097, "界" * 1366, "\ud800", _ForbiddenHash()),
    ids=("ascii-over-budget", "utf8-over-budget", "lone-surrogate", "foreign-object"),
)
def test_invalid_step_id_is_refused_before_plan_iteration_or_sqlite(tmp_path, bad):
    journal, _path, _steps = _fixture(tmp_path)
    journal._steps = _ForbiddenSteps()

    def forbidden_path_access():
        raise AssertionError("invalid step ID touched journal source")

    journal._assert_source_path = forbidden_path_access
    with pytest.raises(
        SyntheticPlanJournalRejected, match="unknown or invalid synthetic plan step",
    ):
        journal.append(bad, StepState.RUNNING, expected_revision=0, at_ms=100)


def test_bounded_known_id_can_still_append_and_restart_without_replay(tmp_path):
    journal, path, steps = _fixture(tmp_path)
    initial = journal.recover()
    assert initial.dispatch_authorized is False
    assert initial.automatic_replay_authorized is False
    running = journal.append(
        "root", StepState.RUNNING, expected_revision=0, at_ms=100,
        retained=initial.tail,
    )
    assert running.ambiguous_running_steps == ("root",)
    cold = SyntheticPlanJournal(path, steps)
    review = cold.recover(retained=initial.tail)
    assert review.ambiguous_running_steps == ("root",)
    assert review.step_statuses == (("root", "running", 1),)
    assert review.dispatch_authorized is False
    assert review.automatic_replay_authorized is False
