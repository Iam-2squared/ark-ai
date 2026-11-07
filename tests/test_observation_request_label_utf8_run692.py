"""Closed Observation fixture reviews respect UTF-8 label byte budgets.

No media acquisition, source authentication, consent, or backend execution is
performed. The review remains in-memory and denies authority even for valid
maximal multibyte labels.
"""

from __future__ import annotations

import pytest

from ark.observation_fixture_chain_review import (
    ObservationFixtureChainRejected,
    review_disconnected_fixture_chain,
)
from ark.observations import ObservationEnvelope, ObservationKind


def _envelope(source: str, scope: str) -> ObservationEnvelope:
    return ObservationEnvelope(
        ObservationKind.TEXT, source, "offline-text", scope,
        100, "a" * 64,
    )


@pytest.mark.parametrize(
    "invalid_label",
    (
        "\ud800",
        "\udfff",
        "é" * 513,
        "あ" * 342,
        "🙂" * 257,
        "\t\n",
    ),
)
@pytest.mark.parametrize("which", ("source", "scope"))
def test_invalid_request_label_rejected_before_fixture_identity_digest(
    invalid_label, which,
):
    source, scope = "fixture-source", "scope:private"
    rows = (_envelope(source, scope),)
    supplied_source = invalid_label if which == "source" else source
    supplied_scope = invalid_label if which == "scope" else scope
    with pytest.raises(ObservationFixtureChainRejected):
        review_disconnected_fixture_chain(
            rows, source_id=supplied_source, privacy_scope=supplied_scope,
        )
    # A failed review cannot mutate the original typed input.
    assert rows[0].source_id == source
    assert rows[0].privacy_scope == scope
    assert rows[0].parent_sha256 is None


@pytest.mark.parametrize(
    "label",
    (
        "x" * 1024,
        "é" * 512,
        "あ" * 341 + "a",
        "🙂" * 256,
    ),
)
@pytest.mark.parametrize("which", ("source", "scope"))
def test_exact_1024_utf8_byte_label_is_valid_but_does_not_grant_authority(
    label, which,
):
    source = label if which == "source" else "fixture-source"
    scope = label if which == "scope" else "scope:private"
    rows = (_envelope(source, scope),)
    reviewed = review_disconnected_fixture_chain(
        rows, source_id=source, privacy_scope=scope,
    )
    again = review_disconnected_fixture_chain(
        rows, source_id=source, privacy_scope=scope,
    )
    assert reviewed == again
    assert reviewed.envelope_count == 1
    assert reviewed.first_observation_id == rows[0].observation_id
    assert reviewed.last_observation_id == rows[0].observation_id
    assert len(reviewed.chain_sha256) == 64
    assert reviewed.source_authenticated is False
    assert reviewed.consent_verified is False
    assert reviewed.dispatch_authorized is False
