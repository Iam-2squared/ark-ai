"""Inert proactive freshness reports cannot run substituted output hooks.

Fixture-only checks: no real notification, external action or trusted clock.
"""

from pathlib import Path

import pytest

import ark.proactive_synthetic_freshness_review as module
from ark.proactive_synthetic_review import (
    SyntheticProactiveLedger,
    SyntheticTriggerPolicy,
    SyntheticTriggerRejected,
)


@pytest.mark.parametrize(
    "member",
    (
        "trigger_id", "prepared_at_ms", "checked_at_ms", "history",
        "__init__", "__getattribute__", "__getattr__",
    ),
)
def test_result_field_or_hook_swap_denied_before_private_sqlite(
    monkeypatch, member,
):
    monkeypatch.setattr(
        module.SyntheticProactiveFreshnessReview, member,
        property(lambda _self: True), raising=False,
    )
    with pytest.raises(SyntheticTriggerRejected, match="carrier definition changed"):
        module.review_prepared_trigger_freshness(
            None, None, None,
            source_digest="a" * 64, observation_digest="b" * 64,
            now_ms=100, max_observation_age_ms=10,
        )


def test_result_type_alias_swap_denied_before_private_sqlite(monkeypatch):
    monkeypatch.setattr(module, "SyntheticProactiveFreshnessReview", object)
    with pytest.raises(SyntheticTriggerRejected, match="carrier definition changed"):
        module.review_prepared_trigger_freshness(
            None, None, None,
            source_digest="a" * 64, observation_digest="b" * 64,
            now_ms=100, max_observation_age_ms=10,
        )


def test_unmodified_fixture_stays_notification_and_dispatch_denied(tmp_path: Path):
    ledger = SyntheticProactiveLedger(tmp_path / "trigger.sqlite")
    policy = SyntheticTriggerPolicy(
        "owner", "notes", "review", 1, "policy-v1", 5, 50, 3,
    )
    receipt = ledger.prepare(
        policy, source_digest="a" * 64, observation_digest="b" * 64,
        observed_at_ms=90, now_ms=100,
    )
    result = module.review_prepared_trigger_freshness(
        ledger, receipt, policy, source_digest="a" * 64,
        observation_digest="b" * 64, now_ms=100, max_observation_age_ms=10,
    )
    assert result.notification_authorized is False
    assert result.dispatch_authorized is False
    assert result.automatic_replay_authorized is False
