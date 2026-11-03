"""Retained freshness preflight cannot silently rebase onto a changed source.

These are offline synthetic SQLite fixtures: no notifications, tool execution,
clock attestation, user consent or permission to replay can be inferred.
"""

from pathlib import Path

import pytest

import ark.proactive_synthetic_freshness_review as module
from ark.proactive_synthetic_continuity_review import read_proactive_witness
from ark.proactive_synthetic_review import (
    SyntheticProactiveLedger,
    SyntheticTriggerPolicy,
    SyntheticTriggerRejected,
)


def _case(tmp_path):
    ledger = SyntheticProactiveLedger(tmp_path / "prepared.sqlite")
    policy = SyntheticTriggerPolicy(
        "offline", "fixture", "reminder", 1, "policy-v1", 5, 50, 3,
    )
    receipt = ledger.prepare(
        policy, source_digest="a" * 64, observation_digest="b" * 64,
        observed_at_ms=90, now_ms=100,
    )
    return ledger, policy, receipt, read_proactive_witness(ledger)


def _review(state):
    ledger, policy, receipt, retained = state
    return module.review_prepared_trigger_freshness(
        ledger, receipt, policy,
        source_digest="a" * 64, observation_digest="b" * 64,
        now_ms=100, max_observation_age_ms=10, retained=retained,
    )


def _clone(value):
    replacement = ("!" + value)[1:]
    assert replacement == value and replacement is not value
    return replacement


@pytest.mark.parametrize(
    "target", ("path", "receipt", "policy", "retained_digest", "retained_rows"),
)
def test_reentrant_retained_validator_cannot_change_initial_epoch(
    tmp_path, monkeypatch, target,
):
    state = _case(tmp_path)
    ledger, policy, receipt, retained = state
    initial_bytes = ledger.path.read_bytes()
    original = module.SyntheticTriggerWitness.assert_integrity
    called = []

    def intervening_validator(self):
        original(self)
        called.append(True)
        if target == "path":
            ledger.path = Path(str(ledger.path))
        elif target == "receipt":
            object.__setattr__(
                receipt, "trigger_id", _clone(receipt.trigger_id),
            )
        elif target == "policy":
            object.__setattr__(
                policy, "policy_revision", _clone(policy.policy_revision),
            )
        elif target == "retained_digest":
            object.__setattr__(retained, "digest", _clone(retained.digest))
        else:
            rows = tuple(list(retained.row_hashes))
            assert rows == retained.row_hashes and rows is not retained.row_hashes
            object.__setattr__(retained, "row_hashes", rows)

    monkeypatch.setattr(
        module.SyntheticTriggerWitness, "assert_integrity",
        intervening_validator,
    )
    with pytest.raises(SyntheticTriggerRejected, match="evidence changed"):
        _review(state)
    assert called == [True]
    assert ledger.path.read_bytes() == initial_bytes


def test_noop_validator_cannot_bless_corrupted_retained_witness(
    tmp_path, monkeypatch,
):
    state = _case(tmp_path)
    retained = state[3]
    object.__setattr__(retained, "digest", "synthetic_triggers_" + "0" * 64)
    monkeypatch.setattr(
        module.SyntheticTriggerWitness, "assert_integrity", lambda self: None,
    )
    with pytest.raises(SyntheticTriggerRejected, match="witness integrity failed"):
        _review(state)


def test_unchanged_retained_witness_stays_readonly_and_deny_only(tmp_path):
    state = _case(tmp_path)
    before = state[0].path.read_bytes()
    review = _review(state)
    assert review.history == state[3]
    assert review.notification_authorized is False
    assert review.dispatch_authorized is False
    assert review.automatic_replay_authorized is False
    assert state[0].path.read_bytes() == before
