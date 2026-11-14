"""Observation/trigger read phases must reject even transient input changes."""

import hashlib
from pathlib import Path

import pytest

import ark.proactive_observation_lineage_fence_review as module
from ark.observations import ObservationEnvelope, ObservationKind
from ark.proactive_synthetic_continuity_review import read_proactive_witness
from ark.proactive_synthetic_review import SyntheticProactiveLedger, SyntheticTriggerPolicy


def _digest(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _fixture(tmp_path: Path):
    parent = ObservationEnvelope(
        ObservationKind.TEXT, "local-source", "fixture:text",
        "local:private", 90, _digest(b"synthetic-parent"),
    )
    child = ObservationEnvelope(
        ObservationKind.TEXT, "local-source", "fixture:text",
        "local:private", 95, _digest(b"synthetic-child"), parent.content_sha256,
    )
    policy = SyntheticTriggerPolicy("owner", "private", "event", 1, "v1", 5, 50, 3)
    ledger = SyntheticProactiveLedger(tmp_path / "triggers.sqlite")
    receipt = ledger.prepare(
        policy, source_digest=module.synthetic_observation_source_digest(child.source_id),
        observation_digest=child.content_sha256, observed_at_ms=95, now_ms=100,
    )
    return (parent, child), child.observation_id, ledger, receipt, policy


def _review(state, **kwargs):
    envelopes, selected, ledger, receipt, policy = state
    options = dict(
        privacy_scope="local:private", ledger=ledger, receipt=receipt,
        policy=policy, now_ms=100, max_age_ms=10,
    )
    options.update(kwargs)
    return module.review_synthetic_observation_trigger(envelopes, selected, **options)


@pytest.mark.parametrize("change", ["envelope", "policy", "receipt"])
def test_transient_input_change_after_first_lineage_fails_before_freshness(
    tmp_path: Path, monkeypatch, change: str,
):
    state = _fixture(tmp_path)
    original = module.review_synthetic_observation_lineage
    freshness_called = 0
    first = True

    def altered(*args, **kwargs):
        nonlocal first
        result = original(*args, **kwargs)
        if first:
            first = False
            if change == "envelope":
                object.__setattr__(state[0][1], "source_id", "another-source")
            elif change == "policy":
                object.__setattr__(state[4], "definition_id", "another-definition")
            else:
                object.__setattr__(state[3], "trigger_id", "trigger_" + "0" * 64)
        return result

    original_freshness = module.review_prepared_trigger_freshness

    def next_phase(*args, **kwargs):
        nonlocal freshness_called
        freshness_called += 1
        return original_freshness(*args, **kwargs)

    monkeypatch.setattr(module, "review_synthetic_observation_lineage", altered)
    monkeypatch.setattr(module, "review_prepared_trigger_freshness", next_phase)
    with pytest.raises(module.SyntheticObservationTriggerRejected, match="changed"):
        _review(state)
    assert freshness_called == 0


def test_retained_history_change_after_freshness_fails_before_next_lineage(
    tmp_path: Path, monkeypatch,
):
    state = _fixture(tmp_path)
    witness = read_proactive_witness(state[2])
    original = module.review_prepared_trigger_freshness
    lineage_called = 0

    def change_witness(*args, **kwargs):
        result = original(*args, **kwargs)
        object.__setattr__(witness, "digest", "synthetic_triggers_" + "0" * 64)
        return result

    original_lineage = module.review_synthetic_observation_lineage

    def next_lineage(*args, **kwargs):
        nonlocal lineage_called
        lineage_called += 1
        return original_lineage(*args, **kwargs)

    monkeypatch.setattr(module, "review_prepared_trigger_freshness", change_witness)
    monkeypatch.setattr(module, "review_synthetic_observation_lineage", next_lineage)
    with pytest.raises(module.SyntheticObservationTriggerRejected, match="witness|changed"):
        _review(state, retained=witness)
    assert lineage_called == 1


def test_stable_retained_review_never_authorizes_capture_or_action(tmp_path: Path):
    state = _fixture(tmp_path)
    outcome = _review(state, retained=read_proactive_witness(state[2]))
    assert outcome.capture_authorized is False
    assert outcome.disclosure_authorized is False
    assert outcome.notification_authorized is False
    assert outcome.dispatch_authorized is False
    assert outcome.automatic_replay_authorized is False
    assert "local-source" not in repr(outcome)
