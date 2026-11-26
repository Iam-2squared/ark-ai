"""Close the observation chain's request-label byte budget at ingress.

A caller-supplied query label is not authenticated provenance or permission to
read fixture data. Test non-ASCII byte boundaries separately from the
ObservationEnvelope's own immutable metadata validation.
"""

from __future__ import annotations

import pytest

from ark.observation_fixture_adapters import fixture_text_observation
from ark.observation_fixture_chain_review import (
    ObservationFixtureChainRejected,
    review_disconnected_fixture_chain,
)
from ark.observations import ObservationKind


@pytest.mark.parametrize("field", ("source_id", "privacy_scope"))
def test_chain_accepts_exact_1024_byte_matching_non_ascii_labels(field):
    label = "🗺" * 256
    kw = {"source_id": "local-source", "privacy_scope": "local:private"}
    kw[field] = label
    envelope = fixture_text_observation(
        "private fixture", kind=ObservationKind.TEXT,
        ingested_at_ms=100, **kw,
    )
    result = review_disconnected_fixture_chain((envelope,), **kw)
    assert len(label.encode("utf-8")) == 1024
    assert result.envelope_count == 1
    assert getattr(result, field) == label
    assert result.source_authenticated is False
    assert result.consent_verified is False
    assert result.dispatch_authorized is False


@pytest.mark.parametrize("field", ("source_id", "privacy_scope"))
@pytest.mark.parametrize("label", ("界" * 342, "🗺" * 257))
def test_chain_rejects_oversized_query_before_fixture_validation(field, label):
    envelope = fixture_text_observation(
        "private fixture", kind=ObservationKind.TEXT, source_id="local-source",
        privacy_scope="local:private", ingested_at_ms=100,
    )
    assert len(label) < 1024
    assert len(label.encode("utf-8")) > 1024
    kw = {"source_id": "local-source", "privacy_scope": "local:private"}
    kw[field] = label
    with pytest.raises(ObservationFixtureChainRejected, match="bounded fixture chain"):
        review_disconnected_fixture_chain((envelope,), **kw)


@pytest.mark.parametrize("field", ("source_id", "privacy_scope"))
def test_chain_rejects_unpaired_surrogates_in_query_label(field):
    envelope = fixture_text_observation(
        "private fixture", kind=ObservationKind.TEXT, source_id="local-source",
        privacy_scope="local:private", ingested_at_ms=100,
    )
    kw = {"source_id": "local-source", "privacy_scope": "local:private"}
    kw[field] = "bad" + chr(0xD800)
    with pytest.raises(ObservationFixtureChainRejected, match="valid UTF-8"):
        review_disconnected_fixture_chain((envelope,), **kw)
