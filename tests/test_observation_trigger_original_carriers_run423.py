"""Observation-trigger correlation retains exact envelope/policy/receipt carriers.

Disposable local trigger ledger and content digests only; no media capture,
notification, Personal Context disclosure, backend action or consent inference.
"""

import hashlib

import pytest

import ark.proactive_observation_lineage_fence_review as review
from ark.observations import ObservationEnvelope, ObservationKind
from ark.proactive_synthetic_continuity_review import read_proactive_witness
from ark.proactive_synthetic_review import SyntheticProactiveLedger, SyntheticTriggerPolicy


def _setup(tmp_path):
    observation = ObservationEnvelope(
        ObservationKind.TEXT, "fixture-source", "fixture:text",
        "private", 95, hashlib.sha256(b"offline-only").hexdigest(),
    )
    policy = SyntheticTriggerPolicy(
        "fixture-owner", "private", "event", 1, "v1", 5, 50, 3,
    )
    ledger = SyntheticProactiveLedger(tmp_path / "trigger.sqlite")
    receipt = ledger.prepare(
        policy,
        source_digest=review.synthetic_observation_source_digest(observation.source_id),
        observation_digest=observation.content_sha256,
        observed_at_ms=95, now_ms=100,
    )
    return observation, policy, ledger, receipt


def _review(state, *, retained=None):
    observation, policy, ledger, receipt = state
    return review.review_synthetic_observation_trigger(
        (observation,), observation.observation_id,
        privacy_scope="private", ledger=ledger, receipt=receipt,
        policy=policy, now_ms=100, max_age_ms=10, retained=retained,
    )


def _clone(value):
    other = ("!" + value)[1:]
    assert other == value and other is not value
    return other


@pytest.mark.parametrize("target", (
    "source_id", "adapter_id", "privacy_scope", "content_sha256",
    "policy_revision", "definition_id", "trigger_id", "retained_digest",
))
def test_review_callback_rejects_equal_value_carrier_replacement(
    tmp_path, monkeypatch, target,
):
    state = _setup(tmp_path)
    retained = read_proactive_witness(state[2])
    native = review.review_prepared_trigger_freshness
    called = []

    def tamper(*args, **kwargs):
        result = native(*args, **kwargs)
        if not called:
            called.append(True)
            if target in {
                "source_id", "adapter_id", "privacy_scope", "content_sha256",
            }:
                subject, field = state[0], target
            elif target in {"policy_revision", "definition_id"}:
                subject, field = state[1], target
            elif target == "trigger_id":
                subject, field = state[3], target
            else:
                subject, field = retained, "digest"
            object.__setattr__(
                subject, field, _clone(getattr(subject, field)),
            )
        return result

    monkeypatch.setattr(review, "review_prepared_trigger_freshness", tamper)
    with pytest.raises(
        review.SyntheticObservationTriggerRejected, match="changed",
    ):
        _review(state, retained=retained)
    assert called == [True]


def test_stable_trigger_review_cannot_dispatch_or_notify(tmp_path):
    state = _setup(tmp_path)
    receipt = _review(state, retained=read_proactive_witness(state[2]))
    assert receipt.trigger_id == state[3].trigger_id
    assert not receipt.capture_authorized
    assert not receipt.disclosure_authorized
    assert not receipt.notification_authorized
    assert not receipt.dispatch_authorized
    assert not receipt.automatic_replay_authorized
    assert "fixture-source" not in repr(receipt)
