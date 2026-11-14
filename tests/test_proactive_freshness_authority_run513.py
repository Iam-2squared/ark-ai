"""Synthetic proactive freshness reports never authorize notifications or replay."""

from __future__ import annotations

from pathlib import Path

import pytest

import ark.proactive_synthetic_freshness_review as module
from ark.proactive_synthetic_review import (
    SyntheticProactiveLedger,
    SyntheticTriggerPolicy,
    SyntheticTriggerRejected,
)


def _case(tmp_path):
    ledger = SyntheticProactiveLedger(tmp_path / "scheduler.sqlite")
    policy = SyntheticTriggerPolicy(
        "fixture", "private", "reminder", 1, "policy-v1", 5, 50, 3,
    )
    receipt = ledger.prepare(
        policy, source_digest="a" * 64, observation_digest="b" * 64,
        observed_at_ms=90, now_ms=100,
    )
    return ledger, policy, receipt


def _review(state):
    ledger, policy, receipt = state
    return module.review_prepared_trigger_freshness(
        ledger, receipt, policy,
        source_digest="a" * 64, observation_digest="b" * 64,
        now_ms=100, max_observation_age_ms=10,
    )


@pytest.mark.parametrize("flag", (
    "notification_authorized",
    "dispatch_authorized",
    "automatic_replay_authorized",
))
@pytest.mark.parametrize("forged", (True, 0))
def test_no_authority_flag_may_claim_permission_or_coerce_false(
    tmp_path, monkeypatch, flag, forged,
):
    state = _case(tmp_path)
    monkeypatch.setattr(
        module.SyntheticProactiveFreshnessReview, flag,
        property(lambda self: forged),
    )
    with pytest.raises(SyntheticTriggerRejected, match="review output changed"):
        _review(state)
    assert state[0].path.exists()


@pytest.mark.parametrize("mutation", ("receipt", "history", "ledger"))
def test_false_authority_getter_cannot_hide_mutated_result_or_source(
    tmp_path, monkeypatch, mutation,
):
    state = _case(tmp_path)
    ledger = state[0]
    calls = 0

    def denial(self):
        nonlocal calls
        calls += 1
        if mutation == "receipt":
            old = self.trigger_id
            substituted = ("!" + old)[1:]
            assert substituted == old and substituted is not old
            object.__setattr__(self, "trigger_id", substituted)
        elif mutation == "history":
            old = self.history.digest
            substituted = ("!" + old)[1:]
            assert substituted == old and substituted is not old
            object.__setattr__(self.history, "digest", substituted)
        else:
            ledger.path = Path(str(ledger.path))
        return False

    monkeypatch.setattr(
        module.SyntheticProactiveFreshnessReview,
        "automatic_replay_authorized",
        property(denial),
    )
    with pytest.raises(SyntheticTriggerRejected, match="review output changed"):
        _review(state)
    # Original descriptor validation rejects the injected getter before calling it.
    assert calls == 0


def test_untouched_due_fixture_stays_read_only_and_inert(tmp_path):
    state = _case(tmp_path)
    before = state[0].path.read_bytes()
    result = _review(state)
    assert result.notification_authorized is False
    assert result.dispatch_authorized is False
    assert result.automatic_replay_authorized is False
    assert result.trigger_id == state[2].trigger_id
    assert state[0].path.read_bytes() == before
