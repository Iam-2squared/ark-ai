"""A closed local observation chain stays source- and privacy-bound.

Mixed TEXT/TRANSCRIPT/IMAGE/SCREEN fixtures only hash in-memory caller bytes;
these local reviews cannot acquire hardware media, authenticate consent,
authorize disclosure, dispatch a tool, or certify capture provenance.
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
from ark.observations import ObservationKind

_SOURCE = "synthetic-device"
_PRIVACY = "local:private"


def _text(data, kind, at, parent=None, *, source=_SOURCE, privacy=_PRIVACY):
    return fixture_text_observation(
        data, kind=kind, source_id=source, privacy_scope=privacy,
        ingested_at_ms=at, parent_sha256=parent,
    )


def _binary(data, kind, at, parent=None, *, source=_SOURCE, privacy=_PRIVACY):
    return fixture_binary_observation(
        data, kind=kind, source_id=source, privacy_scope=privacy,
        ingested_at_ms=at, parent_sha256=parent,
    )


def _review(*envelopes):
    return review_disconnected_fixture_chain(
        tuple(envelopes), source_id=_SOURCE, privacy_scope=_PRIVACY,
    )


def test_mixed_four_kind_chain_is_digest_only_and_denies_all_authority():
    root = _text("offline text", ObservationKind.TEXT, 100)
    transcript = _text(
        "offline transcript", ObservationKind.TRANSCRIPT, 101,
        root.content_sha256,
    )
    image = _binary(
        b"fixture-image", ObservationKind.IMAGE, 102,
        transcript.content_sha256,
    )
    screen = _binary(
        b"fixture-screen", ObservationKind.SCREEN, 103,
        image.content_sha256,
    )
    before = (root, transcript, image, screen)
    review = _review(*before)
    repeat = _review(*before)
    assert review == repeat
    assert review.envelope_count == 4
    assert review.first_observation_id == root.observation_id
    assert review.last_observation_id == screen.observation_id
    assert len(review.chain_sha256) == 64
    assert review.source_authenticated is False
    assert review.consent_verified is False
    assert review.dispatch_authorized is False
    assert not any(hasattr(review, key) for key in ("payload", "text", "image", "raw_bytes"))


@pytest.mark.parametrize(
    ("source", "privacy"),
    (("different-device", _PRIVACY), (_SOURCE, "local:other")),
)
def test_retained_parent_digest_cannot_cross_source_or_privacy_boundary(
    source, privacy,
):
    root = _text("private original", ObservationKind.TEXT, 100)
    child = _binary(
        b"derived fixture", ObservationKind.IMAGE, 101,
        root.content_sha256, source=source, privacy=privacy,
    )
    with pytest.raises(ObservationFixtureChainRejected):
        _review(root, child)


def test_identical_content_from_different_modalities_is_not_unique_parent():
    root = _text("same bytes", ObservationKind.TEXT, 100)
    child = _text(
        "same bytes", ObservationKind.TRANSCRIPT, 101,
        root.content_sha256,
    )
    with pytest.raises(ObservationFixtureChainRejected, match="repeats a content digest"):
        _review(root, child)


@pytest.mark.parametrize("when", (99, 100))
def test_parent_cannot_be_replayed_at_past_or_equal_timestamp(when):
    root = _text("first", ObservationKind.TEXT, 100)
    child = _binary(
        b"later", ObservationKind.SCREEN, when, root.content_sha256,
    )
    with pytest.raises(ObservationFixtureChainRejected):
        _review(root, child)


def test_maximum_closed_chain_remains_digest_only_without_payload_retention():
    observations = []
    parent = None
    for index in range(256):
        row = _text(
            f"local-observation-{index}", ObservationKind.TEXT,
            1000 + index, parent,
        )
        observations.append(row)
        parent = row.content_sha256

    result = _review(*observations)

    assert result.envelope_count == 256
    assert result.first_observation_id == observations[0].observation_id
    assert result.last_observation_id == observations[-1].observation_id
    assert result.source_authenticated is False
    assert result.consent_verified is False
    assert result.dispatch_authorized is False
    assert not hasattr(result, "payload")
    assert not hasattr(result, "raw_bytes")


@pytest.mark.parametrize("length", (0, 257, 512))
def test_unbounded_or_empty_chain_is_rejected_before_any_lineage_review(length):
    root = _text("synthetic payload", ObservationKind.TEXT, 100)
    with pytest.raises(ObservationFixtureChainRejected, match="bounded fixture"):
        _review(*(root for _ in range(length)))


def test_skipping_intermediate_parent_cannot_be_recast_as_closed_lineage():
    root = _text("private root", ObservationKind.TEXT, 100)
    intermediate = _binary(
        b"private image", ObservationKind.IMAGE, 101,
        root.content_sha256,
    )
    bypass = _text(
        "private transcript", ObservationKind.TRANSCRIPT, 102,
        root.content_sha256,
    )

    with pytest.raises(
        ObservationFixtureChainRejected, match="parent or chronology",
    ):
        _review(root, intermediate, bypass)
