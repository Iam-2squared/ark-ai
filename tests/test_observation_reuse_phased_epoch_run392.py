"""Between historical and current checks, observation inputs must remain fixed."""

import hashlib

import pytest

import ark.observation_reuse_review as module
from ark.observation_lineage_review import review_synthetic_observation_lineage
from ark.observations import ObservationEnvelope, ObservationKind


def _state():
    parent_digest = hashlib.sha256(b"synthetic-parent").hexdigest()
    parent = ObservationEnvelope(
        ObservationKind.TEXT, "fixture-source", "adapter-one",
        "private-offline", 100, parent_digest,
    )
    child = ObservationEnvelope(
        ObservationKind.TRANSCRIPT, "fixture-source", "adapter-two",
        "private-offline", 105,
        hashlib.sha256(b"synthetic-child").hexdigest(),
        parent_digest,
    )
    envelopes = (parent, child)
    cached = review_synthetic_observation_lineage(
        envelopes, privacy_scope="private-offline", now_ms=110,
        max_age_ms=20,
    )
    return cached, envelopes


def _reuse(cached, envelopes):
    return module.review_synthetic_observation_reuse(
        cached, envelopes, privacy_scope="private-offline",
        now_ms=115, max_observation_age_ms=20, max_review_age_ms=10,
    )


def test_stable_reuse_remains_diagnostic_only():
    cached, envelopes = _state()
    result = _reuse(cached, envelopes)
    assert result.observation_count == 2
    assert not result.media_capture_authorized
    assert not result.disclosure_authorized
    assert not result.notification_authorized
    assert not result.dispatch_authorized


@pytest.mark.parametrize(
    ("field", "changed"),
    [
        ("adapter_id", "unexpected-adapter"),
        ("source_id", "unexpected-source"),
        ("privacy_scope", "unexpected-scope"),
        ("ingested_at_ms", 101),
        ("content_sha256", "f" * 64),
    ],
)
def test_transient_envelope_forgery_between_lineage_passes_is_rejected(
    monkeypatch, field, changed,
):
    cached, envelopes = _state()
    parent = envelopes[0]
    original_value = getattr(parent, field)
    original_review = module.review_synthetic_observation_lineage
    calls = 0

    def forged_between_passes(*args, **kwargs):
        nonlocal calls
        calls += 1
        if calls == 2:
            object.__setattr__(parent, field, original_value)
        result = original_review(*args, **kwargs)
        if calls == 1:
            object.__setattr__(parent, field, changed)
        return result

    monkeypatch.setattr(
        module, "review_synthetic_observation_lineage", forged_between_passes,
    )
    with pytest.raises(
        module.SyntheticObservationReuseRejected,
        match="cached observation or source changed",
    ):
        _reuse(cached, envelopes)
    assert calls == 1
