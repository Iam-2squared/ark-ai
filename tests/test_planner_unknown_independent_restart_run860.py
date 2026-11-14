"""Disconnected post-COMMIT-UNKNOWN Planner replay with independent branch progress.

A lost response after a committed RUNNING transition cannot be interpreted as
rollback or as permission to replay. No ToolBackend is ever executed.
"""

from __future__ import annotations

import pytest

from ark.agency import planner_journal_review as journal_module
from ark.agency.contracts import PlanConflictError, PlanStep, StepState, ToolCall


def _steps() -> tuple[PlanStep, ...]:
    return (
        PlanStep("root_a", ToolCall("mock", "local.read", "private", {"n": 1})),
        PlanStep(
            "child_a",
            ToolCall("mock", "local.read", "private", {"n": 2}),
            ("root_a",),
        ),
        PlanStep("root_b", ToolCall("mock", "local.read", "private", {"n": 3})),
    )


@pytest.mark.parametrize("terminal", (StepState.SUCCEEDED, StepState.FAILED))
def test_unknown_root_remains_quarantined_while_independent_root_finishes(
    tmp_path, monkeypatch: pytest.MonkeyPatch, terminal: StepState,
) -> None:
    path = tmp_path / "detached-independent.sqlite"
    first = journal_module.SyntheticPlanJournal(path, _steps())
    genesis = first.recover().tail
    original_snapshot = journal_module._checked_snapshot
    after_commit = []

    def lose_response(graph, tail):
        result, verify = original_snapshot(graph, tail)

        def after_durable_commit():
            verify()
            after_commit.append("response-lost")
            raise journal_module.SyntheticPlanJournalRejected(
                "disconnected postcommit response lost"
            )

        return result, after_durable_commit

    with monkeypatch.context() as patch:
        patch.setattr(journal_module, "_checked_snapshot", lose_response)
        with pytest.raises(
            journal_module.SyntheticPlanJournalRejected, match="postcommit",
        ):
            first.append(
                "root_a", StepState.RUNNING, expected_revision=0,
                at_ms=10, retained=genesis,
            )
    assert after_commit == ["response-lost"]

    independent = journal_module.SyntheticPlanJournal(path, _steps())
    after_unknown = independent.recover(retained=genesis)
    assert after_unknown.tail.event_count == 1
    assert after_unknown.ambiguous_running_steps == ("root_a",)
    independent.append(
        "root_b", StepState.RUNNING, expected_revision=0,
        at_ms=20, retained=genesis,
    )
    independent.append(
        "root_b", terminal, expected_revision=1,
        at_ms=30, retained=genesis,
    )

    cold = journal_module.SyntheticPlanJournal(path, _steps())
    recovered = cold.recover(retained=genesis)
    assert recovered.tail.event_count == 3
    assert recovered.ambiguous_running_steps == ("root_a",)
    assert dict(
        (name, (state, revision))
        for name, state, revision in recovered.step_statuses
    ) == {
        "root_a": ("running", 1),
        "child_a": ("pending", 0),
        "root_b": (terminal.value, 2),
    }
    assert recovered.dispatch_authorized is False
    assert recovered.automatic_replay_authorized is False

    with pytest.raises(PlanConflictError):
        cold.append(
            "root_a", StepState.RUNNING, expected_revision=0,
            at_ms=40, retained=genesis,
        )
    with pytest.raises(PlanConflictError, match="dependencies"):
        cold.append(
            "child_a", StepState.RUNNING, expected_revision=0,
            at_ms=40, retained=genesis,
        )
    assert cold.recover(retained=genesis) == recovered
