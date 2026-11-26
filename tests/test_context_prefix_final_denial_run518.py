"""Detached Personal Context prefix report cannot change after a denial callback.

All request IDs are synthetic, content-free local SQLite fixtures. A returned
review does not authorize consent, revocation, disclosure, dispatch or replay.
"""

from __future__ import annotations

import pytest
from test_personal_context_retained_replay_prefix_run511 import _first

import ark.personal_context_replay_ledger as replay
import ark.personal_context_replay_prefix_review as prefix


@pytest.mark.parametrize("mutation", (
    "retained_bool", "current_bool", "status_equal",
    "writer_authority", "consent_authority",
))
def test_final_denial_callback_must_not_change_previous_report_fields(
    tmp_path, monkeypatch: pytest.MonkeyPatch, mutation: str,
) -> None:
    ledger, retained = _first(tmp_path)

    def mutate_and_deny(report: prefix.OfflineContextPrefixReview) -> bool:
        if mutation == "retained_bool":
            object.__setattr__(report, "retained_count", True)
        elif mutation == "current_bool":
            object.__setattr__(report, "current_count", True)
        elif mutation == "status_equal":
            before = report.status
            after = ("_" + before)[1:]
            assert after == before and after is not before
            object.__setattr__(report, "status", after)
        elif mutation == "writer_authority":
            monkeypatch.setattr(
                prefix.OfflineContextPrefixReview,
                "historical_writer_authenticated", property(lambda _: True),
            )
        else:
            monkeypatch.setattr(
                prefix.OfflineContextPrefixReview,
                "consent_verified", property(lambda _: True),
            )
        return False

    with monkeypatch.context() as patch:
        patch.setattr(
            prefix.OfflineContextPrefixReview,
            "automatic_replay_authorized", property(mutate_and_deny),
        )
        with pytest.raises(
            prefix.OfflineContextPrefixRejected, match="changed after denial",
        ):
            prefix.review_retained_context_replay_prefix(ledger, retained)


def test_preinstalled_source_witness_getter_cannot_reach_report(
    tmp_path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    ledger, retained = _first(tmp_path)
    observed: list[prefix.OfflineContextPrefixReview] = []
    witness_calls = []

    def capture_and_deny(report: prefix.OfflineContextPrefixReview) -> bool:
        observed.append(report)
        return False

    def retained_getter(_witness: replay.OfflineContextReplayWitness) -> bool:
        witness_calls.append(True)
        if observed:
            object.__setattr__(observed[-1], "current_count", 0)
        return False

    with monkeypatch.context() as patch:
        patch.setattr(
            prefix.OfflineContextPrefixReview,
            "automatic_replay_authorized", property(capture_and_deny),
        )
        patch.setattr(
            replay.OfflineContextReplayWitness,
            "independent_custody_proven", property(retained_getter),
        )
        with pytest.raises(
            prefix.OfflineContextPrefixRejected,
            match="context result authority changed after denial",
        ):
            prefix.review_retained_context_replay_prefix(ledger, retained)
    # Rejection now occurs before either side-effecting getter or report
    # constructor: the old test's late callback must be unreachable.
    assert not observed
    assert not witness_calls


def test_stable_retained_prefix_report_is_still_inert(tmp_path) -> None:
    ledger, retained = _first(tmp_path)
    result = prefix.review_retained_context_replay_prefix(ledger, retained)
    assert result.retained_count == result.current_count == 1
    assert result.consent_verified is False
    assert result.context_disclosure_authorized is False
    assert result.tool_dispatch_authorized is False
    assert result.automatic_replay_authorized is False
