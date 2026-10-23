"""Proactive freshness receipt rejects reflected mid-review fixture edits."""

from dataclasses import replace
from pathlib import Path

import pytest

from ark.proactive_synthetic_continuity_review import read_proactive_witness
from ark.proactive_synthetic_freshness_review import (
    review_prepared_trigger_freshness,
)
from ark.proactive_synthetic_review import (
    SyntheticProactiveLedger,
    SyntheticTriggerPolicy,
    SyntheticTriggerRejected,
)


def _fixture(tmp_path: Path):
    ledger = SyntheticProactiveLedger(tmp_path / "triggers #1 %.sqlite")
    policy = SyntheticTriggerPolicy(
        "owner", "offline", "trigger", 1, "v1", 5, 50, 3,
    )
    receipt = ledger.prepare(
        policy, source_digest="a" * 64, observation_digest="b" * 64,
        observed_at_ms=90, now_ms=100,
    )
    return ledger, policy, receipt


def _review(state, **kwargs):
    ledger, policy, receipt = state
    options = {
        "source_digest": "a" * 64,
        "observation_digest": "b" * 64,
        "now_ms": 100,
        "max_observation_age_ms": 10,
    }
    options.update(kwargs)
    return review_prepared_trigger_freshness(
        ledger, receipt, policy, **options,
    )


def test_stable_freshness_diagnostic_is_never_execution_approval(tmp_path: Path):
    state = _fixture(tmp_path)
    result = _review(state)
    assert result.notification_authorized is False
    assert result.dispatch_authorized is False
    assert result.automatic_replay_authorized is False
    assert result.prepared_at_ms == state[2].prepared_at_ms
    assert _review(state) == result


@pytest.mark.parametrize("target", ["receipt", "path", "retained"])
def test_reflected_mid_review_evidence_drift_is_denied(
    tmp_path: Path, monkeypatch, target: str,
):
    state = _fixture(tmp_path)
    ledger, policy, receipt = state
    retained = read_proactive_witness(ledger)
    original = SyntheticTriggerPolicy.identity
    calls = []

    def change_on_final_identity(self):
        epoch = original(self)
        calls.append(True)
        if len(calls) == 2:
            if target == "receipt":
                object.__setattr__(receipt, "prepared_at_ms", 101)
            elif target == "path":
                ledger.path = tmp_path / "other.sqlite"
            else:
                object.__setattr__(retained, "row_hashes", ())
        return epoch

    monkeypatch.setattr(SyntheticTriggerPolicy, "identity", change_on_final_identity)
    with pytest.raises(SyntheticTriggerRejected, match="evidence changed"):
        _review(state, retained=retained)
    assert len(calls) == 2


def test_stale_receipt_fails_before_disk_read(tmp_path: Path):
    state = _fixture(tmp_path)
    forged = replace(state[2], prepared_at_ms=99)
    with pytest.raises(SyntheticTriggerRejected, match="persisted prepared marker"):
        _review((state[0], state[1], forged))
