"""Observation witnesses remain genuine inert DTOs under constructor hooks."""

from __future__ import annotations

import pytest

import ark.observation_lineage_review as lineage
import ark.observation_reuse_review as reuse
from ark.observations import ObservationEnvelope, ObservationKind


class ForgedWitness:
    def __init__(self, names, values):
        for name, value in zip(names, values, strict=True):
            setattr(self, name, value)

    @property
    def media_capture_authorized(self) -> bool:
        return True

    @property
    def disclosure_authorized(self) -> bool:
        return True

    @property
    def dispatch_authorized(self) -> bool:
        return True


def fake_type(*names):
    class Substitute(ForgedWitness):
        def __init__(self, *args):
            super().__init__(names, args)

    return Substitute


def envelope():
    return ObservationEnvelope(
        ObservationKind.TEXT, "synthetic:source", "fixture:readonly", "private",
        10, "a" * 64,
    )


def first_review():
    return lineage.review_synthetic_observation_lineage(
        (envelope(),), privacy_scope="private", now_ms=20, max_age_ms=100,
    )


def reuse_review(cached):
    return reuse.review_synthetic_observation_reuse(
        cached, (envelope(),), privacy_scope="private", now_ms=25,
        max_observation_age_ms=100, max_review_age_ms=100,
    )


def test_genuine_lineage_and_reuse_witnesses_remain_deny_only():
    first = first_review()
    second = reuse_review(first)
    assert type(first) is lineage._LINEAGE_RESULT_TYPE
    assert type(second) is reuse._REUSE_RESULT_TYPE
    assert first.media_capture_authorized is False
    assert first.disclosure_authorized is False
    assert second.media_capture_authorized is False
    assert second.dispatch_authorized is False
    assert second.notification_authorized is False


def test_lineage_substituted_constructor_cannot_forge_media_authority(monkeypatch):
    monkeypatch.setattr(lineage, "SyntheticObservationLineageWitness", fake_type(
        "privacy_scope", "checked_at_ms", "observation_count", "lineage_digest",
    ))
    with pytest.raises(lineage.SyntheticObservationLineageRejected, match="result changed"):
        first_review()


def test_reuse_substituted_constructor_cannot_forge_dispatch_authority(monkeypatch):
    cached = first_review()
    monkeypatch.setattr(reuse, "SyntheticObservationReuseReview", fake_type(
        "previous_lineage_digest", "current_lineage_digest",
        "observation_count", "checked_at_ms",
    ))
    with pytest.raises(reuse.SyntheticObservationReuseRejected, match="result changed"):
        reuse_review(cached)


def test_reuse_input_witness_class_is_pinned_not_redefined(monkeypatch):
    cached = first_review()
    monkeypatch.setattr(reuse, "SyntheticObservationLineageWitness", fake_type(
        "privacy_scope", "checked_at_ms", "observation_count", "lineage_digest",
    ))
    # The original cached DTO stays valid even when its exported global name
    # has been replaced; in particular no forged class can change admission.
    result = reuse_review(cached)
    assert type(result) is reuse._REUSE_RESULT_TYPE
    assert result.dispatch_authorized is False
