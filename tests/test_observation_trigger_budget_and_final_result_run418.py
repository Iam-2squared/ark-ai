"""Observation-trigger correlation bounds untrusted metadata and final output.

The source digest and receipt are local fixtures, not sensor authenticity,
privacy consent, notifications or permission for any external ToolBackend.
"""

import hashlib

import pytest

import ark.proactive_observation_lineage_fence_review as module
from ark.observations import ObservationEnvelope, ObservationKind
from ark.proactive_synthetic_review import SyntheticProactiveLedger, SyntheticTriggerPolicy


def _sha(raw):
    return hashlib.sha256(raw).hexdigest()


def _state(tmp_path):
    envelope = ObservationEnvelope(
        ObservationKind.TEXT, "offline-source", "fixture:text",
        "private", 95, _sha(b"content-only-hash"),
    )
    policy = SyntheticTriggerPolicy(
        "owner", "private", "event", 1, "policy-v1", 5, 50, 3,
    )
    ledger = SyntheticProactiveLedger(tmp_path / "trigger.sqlite")
    receipt = ledger.prepare(
        policy,
        source_digest=module.synthetic_observation_source_digest(envelope.source_id),
        observation_digest=envelope.content_sha256,
        observed_at_ms=95, now_ms=100,
    )
    return envelope, policy, ledger, receipt


def _review(state, *, envelopes=None, selected_id=None):
    envelope, policy, ledger, receipt = state
    return module.review_synthetic_observation_trigger(
        (envelope,) if envelopes is None else envelopes,
        envelope.observation_id if selected_id is None else selected_id,
        privacy_scope="private",
        ledger=ledger, receipt=receipt, policy=policy,
        now_ms=100, max_age_ms=10,
    )


@pytest.mark.parametrize("size", (1025, 100_000))
def test_source_identifier_is_bounded_before_hashing(size, monkeypatch):
    hashed = []

    def forbid_hash(*_args):
        hashed.append(True)
        raise AssertionError("over-budget source may not be hashed")

    monkeypatch.setattr(module, "_hash", forbid_hash)
    with pytest.raises(module.SyntheticObservationTriggerRejected, match="bounded"):
        module.synthetic_observation_source_digest("x" * size)
    assert hashed == []


def test_surrogate_source_cannot_reach_json_or_hash():
    with pytest.raises(module.SyntheticObservationTriggerRejected, match="UTF-8"):
        module.synthetic_observation_source_digest("\ud800")


def test_maximum_bounded_source_is_still_deterministic_and_untrusted():
    source = "x" * 1024
    digest = module.synthetic_observation_source_digest(source)
    assert digest == module.synthetic_observation_source_digest(source)
    assert len(digest) == 64


@pytest.mark.parametrize("case", ("empty", "oversized", "selected_id"))
def test_trigger_review_rejects_budget_before_lineage_or_disk(
    tmp_path, monkeypatch, case,
):
    state = _state(tmp_path)
    calls = []

    def forbid(*_args, **_kwargs):
        calls.append(True)
        raise AssertionError("oversized input must not reach lineage")

    monkeypatch.setattr(module, "review_synthetic_observation_lineage", forbid)
    envelope = state[0]
    if case == "empty":
        selection = ()
        selected_id = envelope.observation_id
    elif case == "oversized":
        selection = (envelope,) * 257
        selected_id = envelope.observation_id
    else:
        selection = (envelope,)
        selected_id = "obs_" + "x" * 300
    with pytest.raises(module.SyntheticObservationTriggerRejected, match="exact"):
        _review(state, envelopes=selection, selected_id=selected_id)
    assert calls == []


@pytest.mark.parametrize("mutation", ("returned_digest", "equal_trigger", "source"))
def test_result_constructor_cannot_rewrite_reviewed_metadata(
    tmp_path, monkeypatch, mutation,
):
    state = _state(tmp_path)
    original = module.SyntheticObservationTriggerReview.__init__
    called = []

    def hostile_constructor(self, *args, **kwargs):
        original(self, *args, **kwargs)
        called.append(True)
        if mutation == "returned_digest":
            object.__setattr__(self, "lineage_digest", "olineage_" + "f" * 64)
        elif mutation == "equal_trigger":
            old = self.trigger_id
            alternate = ("!" + old)[1:]
            assert alternate == old and alternate is not old
            object.__setattr__(self, "trigger_id", alternate)
        else:
            object.__setattr__(state[0], "source_id", "other-source")

    monkeypatch.setattr(
        module.SyntheticObservationTriggerReview, "__init__", hostile_constructor,
    )
    with pytest.raises(module.SyntheticObservationTriggerRejected, match="changed"):
        _review(state)
    assert called == [True]


def test_stable_trigger_correlation_is_inert(tmp_path):
    result = _review(_state(tmp_path))
    assert result.lineage_digest.startswith("olineage_")
    assert result.capture_authorized is False
    assert result.disclosure_authorized is False
    assert result.notification_authorized is False
    assert result.dispatch_authorized is False
    assert result.automatic_replay_authorized is False
