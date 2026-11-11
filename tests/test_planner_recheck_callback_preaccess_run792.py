"""Planner detached recovery preflight cannot execute substituted helpers.

No ToolBackend, real WRITE, permission, automatic replay or external effects.
"""

from __future__ import annotations

import pytest

from ark.agency import disconnected_planner_epoch_recheck as epoch
from ark.agency.contracts import PlanStep, ToolCall
from ark.agency.planner_journal_review import SyntheticPlanJournal, SyntheticPlanTail


@pytest.mark.parametrize("target", ("denial_precheck", "tail_assert_shape"))
def test_substituted_recovery_callback_rejected_before_private_read(
    monkeypatch: pytest.MonkeyPatch, target: str,
) -> None:
    called: list[str] = []

    def forbidden(*_args: object, **_kwargs: object) -> None:
        called.append(target)
        raise AssertionError("untrusted Planner callback executed")

    with monkeypatch.context() as patch:
        if target == "denial_precheck":
            patch.setattr(epoch, "_require_original_recovery_denials", forbidden)
        else:
            patch.setattr(SyntheticPlanTail, "assert_shape", forbidden)
        with pytest.raises(
            epoch.PlannerEpochRecheckRejected,
            match="Planner recheck reader epoch changed",
        ):
            epoch.recheck_disconnected_planner_epoch(
                object(), object(), object(),
            )
    assert called == []


def test_unmodified_planner_epoch_is_diagnostic_only(tmp_path) -> None:
    journal = SyntheticPlanJournal(
        tmp_path / "planner-recheck-fixture.sqlite",
        (PlanStep("root", ToolCall("fixture", "read", "local")),),
    )
    recovered = journal.recover()
    report = epoch.recheck_disconnected_planner_epoch(
        journal, recovered, recovered.tail,
    )
    assert report.local_freshness == "MATCH_AT_READ"
    assert report.dispatch_authorized is False
    assert report.automatic_replay_authorized is False
    assert report.freshness_after_return_proven is False
    assert report.manual_review_required is True
