"""Prepared trigger freshness rejects equal-valued carrier substitution.

All inputs are local fixtures. No notification, device or tool is contacted.
"""

import pytest

import ark.proactive_synthetic_freshness_review as module
from ark.proactive_synthetic_continuity_review import read_proactive_witness
from ark.proactive_synthetic_review import (
    SyntheticProactiveLedger,
    SyntheticTriggerPolicy,
    SyntheticTriggerRejected,
)


def _fixture(tmp_path):
    ledger = SyntheticProactiveLedger(tmp_path / "prepared.sqlite")
    policy = SyntheticTriggerPolicy(
        "offline", "fixture", "reminder", 1, "policy-v1", 5, 50, 3,
    )
    receipt = ledger.prepare(
        policy, source_digest="a" * 64, observation_digest="b" * 64,
        observed_at_ms=90, now_ms=100,
    )
    return ledger, policy, receipt


def _review(state, **extras):
    ledger, policy, receipt = state
    return module.review_prepared_trigger_freshness(
        ledger, receipt, policy,
        source_digest="a" * 64, observation_digest="b" * 64,
        now_ms=100, max_observation_age_ms=10, **extras,
    )


def _clone(value):
    copied = value[:3] + value[3:]
    assert copied == value and copied is not value
    return copied


@pytest.mark.parametrize(
    "target", ("policy", "receipt", "retained_rows", "retained_digest"),
)
def test_freshness_rejects_equal_value_carrier_swap(
    tmp_path, monkeypatch, target,
):
    state = _fixture(tmp_path)
    ledger, policy, receipt = state
    retained = read_proactive_witness(ledger)
    original = module._hash
    seen = []

    def intercepted(*args, **kwargs):
        value = original(*args, **kwargs)
        if not seen:
            seen.append(True)
            if target == "policy":
                object.__setattr__(
                    policy, "policy_revision", _clone(policy.policy_revision),
                )
            elif target == "receipt":
                object.__setattr__(
                    receipt, "trigger_id", _clone(receipt.trigger_id),
                )
            elif target == "retained_rows":
                rows = retained.row_hashes
                copied = tuple(list(rows))
                assert copied == rows and copied is not rows
                object.__setattr__(retained, "row_hashes", copied)
            else:
                object.__setattr__(
                    retained, "digest", _clone(retained.digest),
                )
        return value

    monkeypatch.setattr(module, "_hash", intercepted)
    with pytest.raises(SyntheticTriggerRejected, match="evidence changed"):
        _review(state, retained=retained)
    assert seen == [True]


def test_unchanged_retained_freshness_remains_non_authorizing(tmp_path):
    state = _fixture(tmp_path)
    retained = read_proactive_witness(state[0])
    reviewed = _review(state, retained=retained)
    assert reviewed.trigger_id == state[2].trigger_id
    assert reviewed.history == retained
    assert not reviewed.notification_authorized
    assert not reviewed.dispatch_authorized
    assert not reviewed.automatic_replay_authorized
