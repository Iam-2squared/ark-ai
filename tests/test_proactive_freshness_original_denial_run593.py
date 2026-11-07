"""A synthetic freshness report cannot gain an unreviewed authority epoch.

The SQLite preparation and result are offline fixtures only. No notification,
trusted clock, consent, automatic replay or real-world dispatch is authorized.
"""

import pytest

import ark.proactive_synthetic_freshness_review as module
from ark.proactive_synthetic_review import (
    SyntheticProactiveLedger,
    SyntheticTriggerPolicy,
    SyntheticTriggerRejected,
)


def _case(tmp_path):
    ledger = SyntheticProactiveLedger(tmp_path / "freshness-denial.sqlite")
    policy = SyntheticTriggerPolicy(
        "offline", "fixture", "reminder", 1, "policy-v1", 5, 50, 3,
    )
    receipt = ledger.prepare(
        policy, source_digest="a" * 64, observation_digest="b" * 64,
        observed_at_ms=90, now_ms=100,
    )
    return ledger, policy, receipt


def _read(state):
    ledger, policy, receipt = state
    return module.review_prepared_trigger_freshness(
        ledger, receipt, policy,
        source_digest="a" * 64, observation_digest="b" * 64,
        now_ms=100, max_observation_age_ms=10,
    )


@pytest.mark.parametrize("flag", module._FRESHNESS_DENIALS)
def test_equal_false_property_replacement_is_not_original_authority(
    tmp_path, monkeypatch, flag,
):
    state = _case(tmp_path)
    before = state[0].path.read_bytes()
    monkeypatch.setattr(
        module.SyntheticProactiveFreshnessReview,
        flag, property(lambda _: False),
    )
    with pytest.raises(SyntheticTriggerRejected, match="authority epoch"):
        _read(state)
    assert state[0].path.read_bytes() == before


def test_last_getter_cannot_replace_already_checked_denial(
    tmp_path, monkeypatch,
):
    state = _case(tmp_path)
    before = state[0].path.read_bytes()
    review_type = module.SyntheticProactiveFreshnessReview
    original_getattribute = review_type.__getattribute__
    swapped = []

    def late_replace(self, name):
        result = original_getattribute(self, name)
        if name == "automatic_replay_authorized":
            swapped.append(name)
            monkeypatch.setattr(
                review_type, "notification_authorized",
                property(lambda _: False),
            )
        return result

    monkeypatch.setattr(review_type, "__getattribute__", late_replace)
    # An altered lookup hook is now rejected before any getter executes.
    with pytest.raises(
        SyntheticTriggerRejected, match="freshness output carrier definition changed"
    ):
        _read(state)
    assert swapped == []
    assert state[0].path.read_bytes() == before


def test_original_freshness_report_stays_deny_only_and_readonly(tmp_path):
    state = _case(tmp_path)
    before = state[0].path.read_bytes()
    report = _read(state)
    assert report.trigger_id == state[2].trigger_id
    assert report.notification_authorized is False
    assert report.dispatch_authorized is False
    assert report.automatic_replay_authorized is False
    assert state[0].path.read_bytes() == before
