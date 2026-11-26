"""Mixed offline text/image/transcript observation lineage stays non-authorizing.

The adapters receive synthetic bytes supplied by these tests only; they
never open a microphone, camera, screen, file or external data connection.
"""

from dataclasses import replace

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


def _mixed_chain():
    source = "synthetic-local-capture"
    scope = "fixture-private"
    text = fixture_text_observation(
        "raw-fixture-text-903", kind=ObservationKind.TEXT,
        source_id=source, privacy_scope=scope, ingested_at_ms=10,
    )
    image = fixture_binary_observation(
        b"fake-image-bytes-run903", kind=ObservationKind.IMAGE,
        source_id=source, privacy_scope=scope, ingested_at_ms=11,
        parent_sha256=text.content_sha256,
    )
    transcript = fixture_text_observation(
        "raw-fixture-transcript-903", kind=ObservationKind.TRANSCRIPT,
        source_id=source, privacy_scope=scope, ingested_at_ms=12,
        parent_sha256=image.content_sha256,
    )
    screen = fixture_binary_observation(
        b"fake-screen-bytes-run903", kind=ObservationKind.SCREEN,
        source_id=source, privacy_scope=scope, ingested_at_ms=13,
        parent_sha256=transcript.content_sha256,
    )
    return (text, image, transcript, screen)


def test_mixed_modal_fixture_chain_is_digest_only_and_denies_authority():
    chain = _mixed_chain()
    result = review_disconnected_fixture_chain(
        chain, source_id="synthetic-local-capture", privacy_scope="fixture-private",
    )
    assert result.envelope_count == 4
    assert result.first_observation_id == chain[0].observation_id
    assert result.last_observation_id == chain[-1].observation_id
    assert len(result.chain_sha256) == 64
    assert result.source_authenticated is False
    assert result.consent_verified is False
    assert result.dispatch_authorized is False
    displayed = repr(result) + "".join(repr(value) for value in chain)
    assert "raw-fixture-text-903" not in displayed
    assert "raw-fixture-transcript-903" not in displayed
    assert "fake-image-bytes-run903" not in displayed


@pytest.mark.parametrize(
    "change",
    ("out_of_order", "wrong_scope", "time_regression", "repeated_content"),
)
def test_mixed_fixture_rejects_cross_modal_lineage_rewrite(change):
    first, image, transcript, screen = _mixed_chain()
    if change == "out_of_order":
        chain = (first, transcript, image, screen)
    elif change == "wrong_scope":
        chain = (first, replace(image, privacy_scope="unrelated"), transcript, screen)
    elif change == "time_regression":
        chain = (first, replace(image, ingested_at_ms=10), transcript, screen)
    else:
        repeated = fixture_text_observation(
            "raw-fixture-text-903", kind=ObservationKind.TRANSCRIPT,
            source_id="synthetic-local-capture",
            privacy_scope="fixture-private", ingested_at_ms=14,
            parent_sha256=screen.content_sha256,
        )
        chain = (first, image, transcript, screen, repeated)
    with pytest.raises(ObservationFixtureChainRejected):
        review_disconnected_fixture_chain(
            chain, source_id="synthetic-local-capture",
            privacy_scope="fixture-private",
        )
