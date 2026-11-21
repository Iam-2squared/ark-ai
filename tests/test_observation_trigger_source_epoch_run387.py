"""Local observation lineage must preserve the exact trigger ledger source.

Even a successful offline lineage review never authorizes capture or dispatch.
"""

import hashlib
from pathlib import Path

import pytest

import ark.proactive_observation_lineage_fence_review as module
from ark.observations import ObservationEnvelope, ObservationKind
from ark.proactive_synthetic_review import SyntheticProactiveLedger, SyntheticTriggerPolicy


def _hash(value):
    return hashlib.sha256(value).hexdigest()


def _setup(tmp_path):
    parent = ObservationEnvelope(
        ObservationKind.TEXT, "sensitive-source", "fixture:text",
        "fixture:private", 90, _hash(b"private-parent"),
    )
    child = ObservationEnvelope(
        ObservationKind.TEXT, "sensitive-source", "fixture:text",
        "fixture:private", 95, _hash(b"private-child"),
        parent.content_sha256,
    )
    ledger = SyntheticProactiveLedger(tmp_path / "observation # %.sqlite")
    policy = SyntheticTriggerPolicy(
        "fixture-owner", "private", "event", 1, "v1", 5, 50, 3,
    )
    receipt = ledger.prepare(
        policy,
        source_digest=module.synthetic_observation_source_digest(child.source_id),
        observation_digest=child.content_sha256,
        observed_at_ms=95,
        now_ms=100,
    )
    return (parent, child), child.observation_id, ledger, receipt, policy


def _review(state):
    envelopes, selected, ledger, receipt, policy = state
    return module.review_synthetic_observation_trigger(
        envelopes, selected, privacy_scope="fixture:private",
        ledger=ledger, receipt=receipt, policy=policy,
        now_ms=100, max_age_ms=10,
    )


@pytest.mark.parametrize("callback", ["lineage", "freshness"])
@pytest.mark.parametrize("ordinal", [1, 2])
def test_equal_value_path_rebind_between_reviews_is_rejected(
    tmp_path, monkeypatch, callback, ordinal,
):
    state = _setup(tmp_path)
    ledger = state[2]
    original_path = ledger.path
    name = (
        "review_synthetic_observation_lineage" if callback == "lineage"
        else "review_prepared_trigger_freshness"
    )
    original_callback = getattr(module, name)
    count = 0

    def rebound_source(*args, **kwargs):
        nonlocal count
        result = original_callback(*args, **kwargs)
        count += 1
        if count == ordinal:
            ledger.path = Path(str(original_path))
            assert ledger.path == original_path
            assert ledger.path is not original_path
        return result

    monkeypatch.setattr(module, name, rebound_source)
    with pytest.raises(module.SyntheticObservationTriggerRejected, match="source changed"):
        _review(state)
    ledger.path = original_path
    monkeypatch.setattr(module, name, original_callback)
    assert _review(state).dispatch_authorized is False


def test_stable_observation_trigger_review_does_not_authorize_side_effects(tmp_path):
    receipt = _review(_setup(tmp_path))
    assert receipt.capture_authorized is False
    assert receipt.disclosure_authorized is False
    assert receipt.notification_authorized is False
    assert receipt.dispatch_authorized is False
    assert receipt.automatic_replay_authorized is False
    assert "sensitive-source" not in repr(receipt)
