"""Recovered registered READ joins cannot inherit substituted authority flags.

The ToolRegistry, journal, and receipts are synthetic local fixtures. No
backend dispatch, replay, writer identity, or external action is proved.
"""

from __future__ import annotations

import pytest
from test_recovered_registered_read_join_run550 import invoke, make_case

import ark.agency.disconnected_recovered_registered_read_join as joined


@pytest.mark.parametrize(
    "flag",
    (
        "backend_dispatched",
        "write_authorized",
        "automatic_replay_authorized",
        "external_outcome_proven",
        "independent_custody_proven",
    ),
)
def test_preinstalled_false_only_report_denial_is_rejected_before_schedule(
    tmp_path, monkeypatch, flag,
):
    case = make_case(tmp_path)
    observed = []

    def forbidden(*args, **kwargs):
        observed.append("plan verified")
        raise AssertionError("plan must not run under a changed denial")

    try:
        monkeypatch.setattr(joined, "verify_disconnected_batch_plan", forbidden)
        monkeypatch.setattr(
            joined.RecoveredRegisteredReadReview,
            flag,
            property(lambda _self: False),
        )
        with pytest.raises(
            joined.RecoveredRegisteredReadRejected,
            match="recovery carrier changed",
        ):
            invoke(case)
        assert observed == []
        assert case["backend"].calls == 0
        assert not case["gate"]._consumed_tokens
    finally:
        case["journal"].close()


def test_reentrant_plan_checker_cannot_rebaseline_false_report_getter(
    tmp_path, monkeypatch,
):
    case = make_case(tmp_path)
    original = joined.verify_disconnected_batch_plan
    observed = []

    def swap_during_verification(*args, **kwargs):
        value = original(*args, **kwargs)
        observed.append("plan callback")
        monkeypatch.setattr(
            joined.RecoveredRegisteredReadReview,
            "independent_custody_proven",
            property(lambda _self: False),
        )
        return value

    try:
        monkeypatch.setattr(
            joined, "verify_disconnected_batch_plan",
            swap_during_verification,
        )
        with pytest.raises(
            joined.RecoveredRegisteredReadRejected,
            match="recovery carrier changed",
        ):
            invoke(case)
        assert observed == ["plan callback"]
        assert case["backend"].calls == 0
        assert not case["gate"]._consumed_tokens
    finally:
        case["journal"].close()


def test_unchanged_join_remains_disconnected_without_execution(tmp_path):
    case = make_case(tmp_path)
    try:
        result = invoke(case)
        assert type(result) is joined.RecoveredRegisteredReadReview
        assert result.backend_dispatched is False
        assert result.write_authorized is False
        assert result.automatic_replay_authorized is False
        assert result.external_outcome_proven is False
        assert result.independent_custody_proven is False
        assert case["backend"].calls == 0
        assert not case["gate"]._consumed_tokens
    finally:
        case["journal"].close()
