"""Disconnected cross-kind observation chain uses only synthetic fixture bytes.

A valid in-memory chain is not consent, trusted capture, media provenance,
sensor readiness or authorization for subsequent tool execution.
"""

from __future__ import annotations

import pytest

from ark.observation_fixture_adapters import (
    fixture_binary_observation,
    fixture_text_observation,
)
from ark.observation_fixture_chain_review import (
    ObservationFixtureChainRejected,
    review_disconnected_fixture_chain,
)
from ark.observations import ObservationEnvelope, ObservationKind

_SOURCE = "fixture-session"
_PRIVACY = "synthetic-only"


def _chain() -> tuple[ObservationEnvelope, ...]:
    text = fixture_text_observation(
        "explicit fixture only",
        kind=ObservationKind.TEXT, source_id=_SOURCE,
        privacy_scope=_PRIVACY, ingested_at_ms=100,
    )
    image = fixture_binary_observation(
        b"synthetic-image-not-a-camera-frame",
        kind=ObservationKind.IMAGE, source_id=_SOURCE,
        privacy_scope=_PRIVACY, ingested_at_ms=101,
        parent_sha256=text.content_sha256,
    )
    transcript = fixture_text_observation(
        "synthetic transcription, no microphone",
        kind=ObservationKind.TRANSCRIPT, source_id=_SOURCE,
        privacy_scope=_PRIVACY, ingested_at_ms=102,
        parent_sha256=image.content_sha256,
    )
    screen = fixture_binary_observation(
        b"synthetic-screen-not-captured",
        kind=ObservationKind.SCREEN, source_id=_SOURCE,
        privacy_scope=_PRIVACY, ingested_at_ms=103,
        parent_sha256=transcript.content_sha256,
    )
    return (text, image, transcript, screen)


def test_mixed_kind_chain_has_only_local_inert_structural_evidence() -> None:
    items = _chain()
    review = review_disconnected_fixture_chain(
        items, source_id=_SOURCE, privacy_scope=_PRIVACY,
    )
    assert tuple(item.kind for item in items) == (
        ObservationKind.TEXT, ObservationKind.IMAGE,
        ObservationKind.TRANSCRIPT, ObservationKind.SCREEN,
    )
    assert review.envelope_count == 4
    assert review.first_observation_id == items[0].observation_id
    assert review.last_observation_id == items[-1].observation_id
    assert len(review.chain_sha256) == 64
    assert review.source_authenticated is False
    assert review.consent_verified is False
    assert review.dispatch_authorized is False
    assert not hasattr(review, "execute")
    assert not hasattr(review, "capture")


@pytest.mark.parametrize("fault", [
    "source", "privacy", "parent", "clock", "duplicate_digest",
])
def test_mixed_kind_chain_refuses_inconsistent_or_ambiguous_lineage(
    fault: str,
) -> None:
    items = list(_chain())
    target = items[2]
    if fault == "source":
        object.__setattr__(target, "source_id", "different-session")
    elif fault == "privacy":
        object.__setattr__(target, "privacy_scope", "private")
    elif fault == "parent":
        object.__setattr__(target, "parent_sha256", "a" * 64)
    elif fault == "clock":
        object.__setattr__(target, "ingested_at_ms", 100)
    else:
        object.__setattr__(target, "content_sha256", items[1].content_sha256)
    with pytest.raises(ObservationFixtureChainRejected):
        review_disconnected_fixture_chain(
            tuple(items), source_id=_SOURCE, privacy_scope=_PRIVACY,
        )


def test_synthetic_chain_rejects_mismatched_requested_scope() -> None:
    items = _chain()
    with pytest.raises(ObservationFixtureChainRejected):
        review_disconnected_fixture_chain(
            items, source_id=_SOURCE, privacy_scope="some-other-owner",
        )
