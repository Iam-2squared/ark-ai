"""Fixture-only prepared-trigger freshness must preserve per-phase input epochs."""

from pathlib import Path

import pytest

import ark.proactive_synthetic_freshness_review as module
from ark.proactive_synthetic_continuity_review import read_proactive_witness
from ark.proactive_synthetic_review import (
    SyntheticProactiveLedger,
    SyntheticTriggerPolicy,
    SyntheticTriggerRejected,
)


def _fixture(tmp_path):
    ledger = SyntheticProactiveLedger(tmp_path / "proactive # %.sqlite")
    policy = SyntheticTriggerPolicy(
        "offline", "fixture", "trigger", 1, "p1", 5, 100, 3,
    )
    receipt = ledger.prepare(
        policy, source_digest="a" * 64, observation_digest="b" * 64,
        observed_at_ms=90, now_ms=100,
    )
    return ledger, policy, receipt


def _check(state, **kwargs):
    ledger, policy, receipt = state
    return module.review_prepared_trigger_freshness(
        ledger, receipt, policy,
        source_digest="a" * 64, observation_digest="b" * 64,
        now_ms=100, max_observation_age_ms=10, **kwargs,
    )


def test_unchanged_freshness_never_grants_action(tmp_path):
    state = _fixture(tmp_path)
    proof = read_proactive_witness(state[0])
    reviewed = _check(state, retained=proof)
    assert reviewed.trigger_id == state[2].trigger_id
    assert reviewed.history == proof
    assert not reviewed.notification_authorized
    assert not reviewed.dispatch_authorized
    assert not reviewed.automatic_replay_authorized


@pytest.mark.parametrize("target", ["source", "receipt", "policy", "retained"])
def test_validate_phase_transient_drift_cannot_hide_in_next_digest(
    tmp_path, monkeypatch, target,
):
    state = _fixture(tmp_path)
    ledger, policy, receipt = state
    witness = read_proactive_witness(ledger)
    original_path = ledger.path
    original_validate = module._validate
    original_digest = module._digest

    def mutate():
        if target == "source":
            ledger.path = Path(str(original_path))
        elif target == "receipt":
            object.__setattr__(receipt, "prepared_at_ms", 99)
        elif target == "policy":
            object.__setattr__(policy, "minimum_interval_ms", 6)
        else:
            object.__setattr__(witness, "digest", "synthetic_triggers_" + "0" * 64)

    def restore():
        if target == "source":
            ledger.path = original_path
        elif target == "receipt":
            object.__setattr__(receipt, "prepared_at_ms", 100)
        elif target == "policy":
            object.__setattr__(policy, "minimum_interval_ms", 5)
        else:
            object.__setattr__(
                witness, "digest", read_proactive_witness(ledger).digest,
            )

    def after_validation(conn):
        original_validate(conn)
        mutate()

    def restore_during_digest(label, value):
        restore()
        return original_digest(label, value)

    monkeypatch.setattr(module, "_validate", after_validation)
    monkeypatch.setattr(module, "_digest", restore_during_digest)
    with pytest.raises(SyntheticTriggerRejected, match="evidence changed"):
        _check(state, retained=witness)


def test_continuity_callback_swap_before_final_identity_is_denied(
    tmp_path, monkeypatch,
):
    state = _fixture(tmp_path)
    ledger, policy, receipt = state
    witness = read_proactive_witness(ledger)
    original_continuity = module.assert_proactive_history_continues
    original_identity = SyntheticTriggerPolicy.identity
    calls = 0

    def drift_after_continuity(older, current):
        original_continuity(older, current)
        object.__setattr__(receipt, "prepared_at_ms", 99)

    def restore_at_final_identity(self):
        nonlocal calls
        calls += 1
        if calls == 2:
            object.__setattr__(receipt, "prepared_at_ms", 100)
        return original_identity(self)

    monkeypatch.setattr(
        module, "assert_proactive_history_continues", drift_after_continuity,
    )
    monkeypatch.setattr(
        SyntheticTriggerPolicy, "identity", restore_at_final_identity,
    )
    with pytest.raises(SyntheticTriggerRejected, match="evidence changed"):
        _check(state, retained=witness)
    assert calls == 1
