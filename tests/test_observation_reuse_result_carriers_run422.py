"""A reused observation witness must survive every offline review callback.

No media capture, disclosure, consent or ToolBackend execution is involved.
"""

import hashlib

import pytest

import ark.observation_reuse_review as reuse
from ark.observation_lineage_review import review_synthetic_observation_lineage
from ark.observations import ObservationEnvelope, ObservationKind


def _fixture():
    item = ObservationEnvelope(
        ObservationKind.TEXT, "fixture-source", "fixture-adapter",
        "fixture-private", 100, hashlib.sha256(b"offline-data").hexdigest(),
    )
    envelopes = (item,)
    cached = review_synthetic_observation_lineage(
        envelopes, privacy_scope="fixture-private", now_ms=105, max_age_ms=20,
    )
    return cached, envelopes


def _review(cached, envelopes):
    return reuse.review_synthetic_observation_reuse(
        cached, envelopes, privacy_scope="fixture-private", now_ms=110,
        max_observation_age_ms=20, max_review_age_ms=10,
    )


def _equal_fresh_string(value):
    copy = ("!" + value)[1:]
    assert copy == value and copy is not value
    return copy


@pytest.mark.parametrize("field", ("privacy_scope", "lineage_digest"))
def test_historical_callback_cannot_swap_equal_cached_carrier(
    monkeypatch, field,
):
    cached, envelopes = _fixture()
    original = reuse.review_synthetic_observation_lineage

    def mutate(*args, **kwargs):
        result = original(*args, **kwargs)
        object.__setattr__(
            cached, field, _equal_fresh_string(getattr(cached, field)),
        )
        return result

    monkeypatch.setattr(reuse, "review_synthetic_observation_lineage", mutate)
    with pytest.raises(reuse.SyntheticObservationReuseRejected, match="changed"):
        _review(cached, envelopes)


@pytest.mark.parametrize("field", ("source_id", "content_sha256"))
def test_first_review_cannot_swap_equal_envelope_carrier(
    monkeypatch, field,
):
    cached, envelopes = _fixture()
    original = reuse.review_synthetic_observation_lineage

    def mutate(*args, **kwargs):
        result = original(*args, **kwargs)
        object.__setattr__(
            envelopes[0], field,
            _equal_fresh_string(getattr(envelopes[0], field)),
        )
        return result

    monkeypatch.setattr(reuse, "review_synthetic_observation_lineage", mutate)
    with pytest.raises(reuse.SyntheticObservationReuseRejected, match="changed"):
        _review(cached, envelopes)


@pytest.mark.parametrize("target", ("cached", "current", "result"))
def test_result_constructor_cannot_mutate_prior_witnesses_or_receipt(
    monkeypatch, target,
):
    cached, envelopes = _fixture()
    original_review = reuse.review_synthetic_observation_lineage
    original_init = reuse.SyntheticObservationReuseReview.__init__
    current = []

    def retain_current(*args, **kwargs):
        result = original_review(*args, **kwargs)
        if kwargs["now_ms"] == 110:
            current.append(result)
        return result

    def forged_init(self, *args, **kwargs):
        original_init(self, *args, **kwargs)
        if target == "cached":
            object.__setattr__(
                cached, "lineage_digest",
                _equal_fresh_string(cached.lineage_digest),
            )
        elif target == "current":
            object.__setattr__(
                current[0], "lineage_digest",
                _equal_fresh_string(current[0].lineage_digest),
            )
        else:
            object.__setattr__(self, "observation_count", 42)

    monkeypatch.setattr(
        reuse, "review_synthetic_observation_lineage", retain_current,
    )
    monkeypatch.setattr(reuse.SyntheticObservationReuseReview, "__init__", forged_init)
    with pytest.raises(reuse.SyntheticObservationReuseRejected, match="changed"):
        _review(cached, envelopes)
    assert len(current) == 1


def test_forged_current_lineage_result_is_rejected(monkeypatch):
    cached, envelopes = _fixture()
    original = reuse.review_synthetic_observation_lineage

    def forged(*args, **kwargs):
        result = original(*args, **kwargs)
        if kwargs["now_ms"] == 110:
            object.__setattr__(result, "observation_count", 999)
        return result

    monkeypatch.setattr(reuse, "review_synthetic_observation_lineage", forged)
    with pytest.raises(reuse.SyntheticObservationReuseRejected, match="current"):
        _review(cached, envelopes)


def test_unchanged_reuse_receipt_remains_inert():
    cached, envelopes = _fixture()
    result = _review(cached, envelopes)
    assert result.observation_count == 1
    assert result.previous_lineage_digest == cached.lineage_digest
    assert not result.media_capture_authorized
    assert not result.disclosure_authorized
    assert not result.notification_authorized
    assert not result.dispatch_authorized
