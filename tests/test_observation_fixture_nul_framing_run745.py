"""NUL-delimited observation lineage framing is unambiguous or rejected.

All envelopes are disconnected text fixtures, not live sensors or permissions.
"""

from __future__ import annotations

import hashlib

import pytest

from ark.observation_fixture_adapters import fixture_text_observation
from ark.observation_fixture_chain_review import (
    ObservationFixtureChainRejected,
    review_disconnected_fixture_chain,
)
from ark.observations import ObservationEnvelope, ObservationKind


def _fixture(source: str, privacy: str):
    return fixture_text_observation(
        "synthetic local content",
        kind=ObservationKind.TEXT,
        source_id=source,
        privacy_scope=privacy,
        ingested_at_ms=100,
    )


@pytest.mark.parametrize(("source", "privacy"), (
    ("a\x00b", "c"),
    ("a", "b\x00c"),
    ("\x00fixture", "private"),
    ("fixture\x00", "private"),
    ("fixture", "\x00private"),
    ("fixture", "private\x00"),
))
def test_embedded_nul_cannot_confuse_chain_digest_field_framing(
    source, privacy,
):
    # The disconnected adapter now rejects NUL labels BEFORE hashing private
    # fixture bytes. Keep this stricter boundary; do not relax its preflight.
    with pytest.raises(ValueError, match="contains a NUL separator"):
        _fixture(source, privacy)

    # The frozen, inert v1 envelope still permits a NUL label. Construct it
    # directly to retain the independent chain reviewer's framing regression.
    item = ObservationEnvelope(
        kind=ObservationKind.TEXT,
        source_id=source,
        adapter_id="fixture:text:v1",
        privacy_scope=privacy,
        ingested_at_ms=100,
        content_sha256=hashlib.sha256(b"synthetic local content").hexdigest(),
    )
    assert item.source_id == source
    assert item.privacy_scope == privacy
    with pytest.raises(
        ObservationFixtureChainRejected, match="exact bounded fixture chain",
    ):
        review_disconnected_fixture_chain(
            (item,), source_id=source, privacy_scope=privacy,
        )


def test_distinct_valid_labels_still_produce_disconnected_denial_receipts():
    first = _fixture("fixture", "private")
    second = _fixture("fixture", "private:other")
    one = review_disconnected_fixture_chain(
        (first,), source_id="fixture", privacy_scope="private",
    )
    two = review_disconnected_fixture_chain(
        (second,), source_id="fixture", privacy_scope="private:other",
    )
    assert one.chain_sha256 != two.chain_sha256
    assert one.source_authenticated is False
    assert one.consent_verified is False
    assert one.dispatch_authorized is False
    assert two.dispatch_authorized is False
