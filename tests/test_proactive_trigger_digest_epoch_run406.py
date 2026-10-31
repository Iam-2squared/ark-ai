"""Offline trigger digests cannot mask transient policy or source retargeting.

Fixture preparation writes only inert local SQLite markers; never notifications,
real ToolBackend work, clocks, or user-visible actions.
"""

from pathlib import Path

import pytest

import ark.proactive_synthetic_review as proactive
from ark.proactive_synthetic_review import (
    SyntheticProactiveLedger,
    SyntheticTriggerPolicy,
    SyntheticTriggerRejected,
)


def _fixture(tmp_path):
    ledger = SyntheticProactiveLedger(tmp_path / "trigger.sqlite")
    policy = SyntheticTriggerPolicy(
        "offline-owner", "private", "fixture", 1, "rev1", 1, 100, 3,
    )
    return ledger, policy


def _prepare(ledger, policy):
    return ledger.prepare(
        policy,
        source_digest="a" * 64, observation_digest="b" * 64,
        observed_at_ms=10, now_ms=10,
    )


@pytest.mark.parametrize(
    "stage",
    ("ARK-trigger-scope-v1", "ARK-trigger-policy-v1", "ARK-trigger-occurrence-v1"),
)
def test_each_trigger_digest_refuses_policy_retarget_before_sqlite(
    tmp_path, monkeypatch, stage,
):
    ledger, policy = _fixture(tmp_path)
    original_hash = proactive._hash
    phases = []

    def hashing(label, fields):
        result = original_hash(label, fields)
        phases.append(label)
        if label == stage:
            object.__setattr__(policy, "revision", 2)
        return result

    monkeypatch.setattr(proactive, "_hash", hashing)
    with pytest.raises(SyntheticTriggerRejected, match="during trigger digest"):
        _prepare(ledger, policy)
    assert phases[-1] == stage
    assert ledger.count() == 0


def test_scope_callback_drift_cannot_be_restored_by_next_digest(
    tmp_path, monkeypatch,
):
    ledger, policy = _fixture(tmp_path)
    original_hash = proactive._hash
    phases = []

    def hashing(label, fields):
        result = original_hash(label, fields)
        if label == "ARK-trigger-scope-v1":
            object.__setattr__(policy, "revision", 2)
            phases.append("retarget")
        elif label == "ARK-trigger-policy-v1":
            object.__setattr__(policy, "revision", 1)
            phases.append("restore")
        return result

    monkeypatch.setattr(proactive, "_hash", hashing)
    with pytest.raises(SyntheticTriggerRejected, match="during trigger digest"):
        _prepare(ledger, policy)
    assert phases == ["retarget"]
    assert ledger.count() == 0


def test_equal_valued_sqlite_path_swap_during_hash_is_rejected(
    tmp_path, monkeypatch,
):
    ledger, policy = _fixture(tmp_path)
    original_hash = proactive._hash
    path = ledger.path

    def hashing(label, fields):
        result = original_hash(label, fields)
        if label == "ARK-trigger-scope-v1":
            ledger.path = Path(str(path))
            assert ledger.path == path
            assert ledger.path is not path
        return result

    monkeypatch.setattr(proactive, "_hash", hashing)
    with pytest.raises(SyntheticTriggerRejected, match="during trigger digest"):
        _prepare(ledger, policy)
    assert ledger.count() == 0


def test_stable_offline_preparation_preserves_no_dispatch_and_restart(tmp_path):
    ledger, policy = _fixture(tmp_path)
    receipt = _prepare(ledger, policy)
    assert receipt.trigger_id.startswith("trigger_")
    assert not receipt.notification_authorized
    assert not receipt.dispatch_authorized
    assert not receipt.automatic_replay_authorized
    assert SyntheticProactiveLedger(ledger.path).count() == 1
