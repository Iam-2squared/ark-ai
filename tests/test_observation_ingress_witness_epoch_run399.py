"""Observation-trigger diagnostics pin inputs before their first callback.

Retained trigger hashes and supplied observation metadata are not trusted
consent, capture evidence or notification authority.
"""

import hashlib

import pytest

import ark.proactive_observation_lineage_fence_review as observation
from ark.observations import ObservationEnvelope, ObservationKind
from ark.proactive_synthetic_continuity_review import (
    SyntheticTriggerWitness,
    read_proactive_witness,
)
from ark.proactive_synthetic_review import SyntheticProactiveLedger, SyntheticTriggerPolicy


def _fixture(tmp_path):
    envelope = ObservationEnvelope(
        ObservationKind.TEXT, "fixture-source", "fixture:text", "local:private",
        95, hashlib.sha256(b"synthetic input").hexdigest(),
    )
    policy = SyntheticTriggerPolicy(
        "fixture-owner", "fixture-space", "event", 1, "policy-v1", 5, 50, 3,
    )
    ledger = SyntheticProactiveLedger(tmp_path / "triggers.sqlite")
    receipt = ledger.prepare(
        policy,
        source_digest=observation.synthetic_observation_source_digest(envelope.source_id),
        observation_digest=envelope.content_sha256, observed_at_ms=95, now_ms=100,
    )
    return envelope, policy, ledger, receipt, read_proactive_witness(ledger)


def _review(state):
    envelope, policy, ledger, receipt, retained = state
    return observation.review_synthetic_observation_trigger(
        (envelope,), envelope.observation_id,
        privacy_scope="local:private", ledger=ledger,
        receipt=receipt, policy=policy,
        now_ms=100, max_age_ms=10, retained=retained,
    )


@pytest.mark.parametrize("target", ("equal_rows", "digest", "policy"))
def test_retained_integrity_callback_cannot_rebase_observation_review(
    tmp_path, monkeypatch, target,
):
    state = _fixture(tmp_path)
    _, policy, _, _, retained = state
    original_rows = retained.row_hashes
    original_digest = retained.digest
    original_policy = policy.definition_id
    original = SyntheticTriggerWitness.assert_integrity
    calls = 0

    def mutate_after_integrity(self):
        nonlocal calls
        original(self)
        if self is retained:
            calls += 1
            if target == "equal_rows":
                new_rows = tuple(list(original_rows))
                assert new_rows == original_rows and new_rows is not original_rows
                object.__setattr__(retained, "row_hashes", new_rows)
            elif target == "digest":
                object.__setattr__(retained, "digest", "synthetic_triggers_" + "0" * 64)
            else:
                object.__setattr__(policy, "definition_id", "other-definition")

    monkeypatch.setattr(SyntheticTriggerWitness, "assert_integrity", mutate_after_integrity)

    def forbidden_lineage(*args, **kwargs):
        raise AssertionError("invalid inputs must be denied before first lineage review")

    monkeypatch.setattr(
        observation, "review_synthetic_observation_lineage", forbidden_lineage,
    )
    with pytest.raises(observation.SyntheticObservationTriggerRejected, match="changed"):
        _review(state)
    assert calls == 1

    monkeypatch.undo()
    object.__setattr__(retained, "row_hashes", original_rows)
    object.__setattr__(retained, "digest", original_digest)
    object.__setattr__(policy, "definition_id", original_policy)
    assert _review(state).dispatch_authorized is False


def test_source_digest_callback_cannot_retarget_observation_before_lineage(
    tmp_path, monkeypatch,
):
    state = _fixture(tmp_path)
    envelope = state[0]
    old_source = envelope.source_id
    original = observation.synthetic_observation_source_digest
    calls = 0

    def source_digest_with_mutation(source_id):
        nonlocal calls
        result = original(source_id)
        calls += 1
        object.__setattr__(envelope, "source_id", "other-source")
        return result

    monkeypatch.setattr(
        observation, "synthetic_observation_source_digest",
        source_digest_with_mutation,
    )

    def forbidden_lineage(*args, **kwargs):
        raise AssertionError("source mutation cannot reach lineage reviewer")

    monkeypatch.setattr(
        observation, "review_synthetic_observation_lineage", forbidden_lineage,
    )
    with pytest.raises(observation.SyntheticObservationTriggerRejected, match="changed"):
        _review(state)
    assert calls == 1

    monkeypatch.undo()
    object.__setattr__(envelope, "source_id", old_source)
    result = _review(state)
    assert result.capture_authorized is False
    assert result.notification_authorized is False
