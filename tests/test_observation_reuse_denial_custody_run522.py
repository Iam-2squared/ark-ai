"""A fresh synthetic observation does not grant capture/disclosure/dispatch.

No camera, microphone, network, notification, or external ToolBackend is used.
"""

import hashlib

import pytest

from ark.observation_lineage_review import review_synthetic_observation_lineage
from ark.observation_reuse_review import (
    SyntheticObservationReuseRejected,
    SyntheticObservationReuseReview,
    review_synthetic_observation_reuse,
)
from ark.observations import ObservationEnvelope, ObservationKind


def _case():
    envelope = ObservationEnvelope(
        ObservationKind.TEXT,
        "fixture-source",
        "fixture-adapter",
        "private-fixture",
        100,
        hashlib.sha256(b"private synthetic bytes").hexdigest(),
    )
    sources = (envelope,)
    cached = review_synthetic_observation_lineage(
        sources, privacy_scope="private-fixture", now_ms=105,
        max_age_ms=20,
    )
    return sources, cached


def _invoke(sources, cached):
    return review_synthetic_observation_reuse(
        cached, sources, privacy_scope="private-fixture", now_ms=110,
        max_observation_age_ms=20, max_review_age_ms=10,
    )


@pytest.mark.parametrize(
    "authority",
    (
        "media_capture_authorized",
        "disclosure_authorized",
        "notification_authorized",
        "dispatch_authorized",
    ),
)
def test_reuse_never_accepts_authorizing_property(monkeypatch, authority):
    sources, cached = _case()
    monkeypatch.setattr(
        SyntheticObservationReuseReview, authority, property(lambda self: True),
    )
    with pytest.raises(SyntheticObservationReuseRejected, match="authority"):
        _invoke(sources, cached)


@pytest.mark.parametrize(
    ("field", "changed"),
    (
        ("previous_lineage_digest", "f" * 64),
        ("current_lineage_digest", "f" * 64),
        ("observation_count", 900),
        ("checked_at_ms", 1000),
    ),
)
def test_false_last_denial_cannot_mutate_returned_receipt(
    monkeypatch, field, changed,
):
    sources, cached = _case()

    def mutate(self):
        object.__setattr__(self, field, changed)
        return False

    monkeypatch.setattr(
        SyntheticObservationReuseReview, "dispatch_authorized", property(mutate),
    )
    with pytest.raises(SyntheticObservationReuseRejected, match="changed"):
        _invoke(sources, cached)


@pytest.mark.parametrize("target", ("cached", "source"))
def test_false_last_denial_cannot_retarget_original_lineage(
    monkeypatch, target,
):
    sources, cached = _case()

    def mutate(self):
        if target == "cached":
            object.__setattr__(cached, "lineage_digest", "f" * 64)
        else:
            object.__setattr__(sources[0], "source_id", "other-source")
        return False

    monkeypatch.setattr(
        SyntheticObservationReuseReview, "dispatch_authorized", property(mutate),
    )
    with pytest.raises(SyntheticObservationReuseRejected, match="changed"):
        _invoke(sources, cached)


def test_clean_reuse_still_returns_local_diagnostic():
    sources, cached = _case()
    result = _invoke(sources, cached)
    assert result.observation_count == 1
    assert result.checked_at_ms == 110
    assert result.media_capture_authorized is False
    assert result.disclosure_authorized is False
    assert result.notification_authorized is False
    assert result.dispatch_authorized is False
