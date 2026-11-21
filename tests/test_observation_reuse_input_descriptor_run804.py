"""Reject substituted private lineage getters before invocation.

All inputs are synthetic, memory-only; nothing captures or exports media.
"""

import hashlib

import pytest

import ark.observation_reuse_review as reuse
from ark.observation_lineage_review import review_synthetic_observation_lineage
from ark.observations import ObservationEnvelope, ObservationKind


def _state():
    source = ObservationEnvelope(
        ObservationKind.TEXT, "fixture", "adapter", "private-test", 100,
        hashlib.sha256(b"inert fixture").hexdigest(),
    )
    cached = review_synthetic_observation_lineage(
        (source,), privacy_scope="private-test", now_ms=105, max_age_ms=30,
    )
    return cached, (source,)


def _review(cached, sources):
    return reuse.review_synthetic_observation_reuse(
        cached, sources, privacy_scope="private-test", now_ms=110,
        max_observation_age_ms=30, max_review_age_ms=10,
    )


@pytest.mark.parametrize(("target", "field"), (
    ("cached", "privacy_scope"),
    ("cached", "lineage_digest"),
    ("source", "source_id"),
    ("source", "privacy_scope"),
    ("source", "observation_id"),
))
def test_private_input_class_getter_is_rejected_before_access(
    monkeypatch, target, field,
):
    cached, sources = _state()
    accessed = []

    def hostile(_self):
        accessed.append(field)
        return "private-test"

    carrier = type(cached) if target == "cached" else type(sources[0])
    monkeypatch.setattr(carrier, field, property(hostile))
    with pytest.raises(
        reuse.SyntheticObservationReuseRejected,
        match="observation reuse input descriptor changed",
    ):
        _review(cached, sources)
    assert accessed == []


def test_historical_callback_cannot_install_a_late_private_getter(monkeypatch):
    cached, sources = _state()
    original = reuse.review_synthetic_observation_lineage
    accessed = []
    calls = []

    def changed(_self):
        accessed.append("private")
        return "fixture"

    def inject(*args, **kwargs):
        witness = original(*args, **kwargs)
        calls.append(1)
        monkeypatch.setattr(ObservationEnvelope, "adapter_id", property(changed))
        return witness

    monkeypatch.setattr(reuse, "review_synthetic_observation_lineage", inject)
    with pytest.raises(
        reuse.SyntheticObservationReuseRejected,
        match="observation reuse input descriptor changed",
    ):
        _review(cached, sources)
    assert len(calls) == 1
    assert accessed == []


def test_unmodified_cached_lineage_still_yields_only_denied_authority():
    outcome = _review(*_state())
    assert outcome.observation_count == 1
    assert outcome.checked_at_ms == 110
    assert outcome.media_capture_authorized is False
    assert outcome.disclosure_authorized is False
    assert outcome.notification_authorized is False
    assert outcome.dispatch_authorized is False
