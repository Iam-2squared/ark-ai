"""An age-fresh ObservationWindow is not proof of a closed fixture lineage.

Private synthetic envelope metadata can satisfy a local age/scope window
while failing an independent source/parent/chronology/content-uniqueness
review. Neither reviewer authorizes media capture, consent or disclosure.
"""

from __future__ import annotations

import pytest

from ark.observation_fixture_chain_review import (
    ObservationFixtureChainRejected,
    review_disconnected_fixture_chain,
)
from ark.observation_window_review import ObservationWindowReview
from ark.observations import ObservationEnvelope, ObservationKind


def _row(kind, source, adapter, at_ms, digest, parent=None):
    return ObservationEnvelope(
        kind, source, adapter, "private-fixture",
        at_ms, digest, parent,
    )


def _pair(modification=None):
    root = _row(ObservationKind.TEXT, "offline", "text", 100, "a" * 64)
    child = _row(
        ObservationKind.TRANSCRIPT, "offline", "transcript",
        110, "b" * 64, root.content_sha256,
    )
    if modification == "skipped_parent":
        child = _row(
            ObservationKind.TRANSCRIPT, "offline", "transcript",
            110, "b" * 64, "c" * 64,
        )
    elif modification == "duplicate_digest":
        child = _row(
            ObservationKind.TRANSCRIPT, "offline", "transcript",
            110, root.content_sha256, root.content_sha256,
        )
    elif modification == "nonincreasing_time":
        child = _row(
            ObservationKind.TRANSCRIPT, "offline", "transcript",
            100, "b" * 64, root.content_sha256,
        )
    elif modification == "different_source":
        child = _row(
            ObservationKind.TRANSCRIPT, "other-offline", "transcript",
            110, "b" * 64, root.content_sha256,
        )
    return root, child


def test_valid_window_and_closed_chain_are_distinct_non_authorizing_reviews():
    rows = _pair()
    window = ObservationWindowReview("private-fixture", 130, 30, rows)
    chain = review_disconnected_fixture_chain(
        rows, source_id="offline", privacy_scope="private-fixture",
    )
    assert chain.envelope_count == 2
    assert chain.first_observation_id == rows[0].observation_id
    assert chain.last_observation_id == rows[1].observation_id
    assert len(chain.chain_sha256) == 64
    assert window.witness.startswith("window_")
    window.assert_fresh_at(130)
    with pytest.raises(ValueError, match="age budget"):
        window.assert_fresh_at(131)
    assert chain.source_authenticated is False
    assert chain.consent_verified is False
    assert chain.dispatch_authorized is False


@pytest.mark.parametrize(
    "modification",
    ("skipped_parent", "duplicate_digest",
     "nonincreasing_time", "different_source"),
)
def test_age_fresh_window_does_not_launder_invalid_closed_lineage(modification):
    rows = _pair(modification)
    window = ObservationWindowReview("private-fixture", 130, 30, rows)
    window.assert_fresh_at(130)
    assert window.witness.startswith("window_")
    with pytest.raises(ObservationFixtureChainRejected):
        review_disconnected_fixture_chain(
            rows, source_id="offline", privacy_scope="private-fixture",
        )
