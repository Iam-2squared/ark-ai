"""Content-identical mixed modalities are not distinct closed-lineage parents.

The offline fixture adapters never access media devices or remote services.
A changed modality or adapter may yield a new observation ID, but identical
content digests remain an ambiguous ancestor in a closed synthetic chain.
Neither well-formed chain nor local checksum establishes consent/provenance.
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
_SCOPE = "scope:private"


def _fixture(kind, payload, timestamp, parent=None):
    common = {
        "kind": kind,
        "source_id": _SOURCE,
        "privacy_scope": _SCOPE,
        "ingested_at_ms": timestamp,
        "parent_sha256": parent,
    }
    if kind in (ObservationKind.TEXT, ObservationKind.TRANSCRIPT):
        return fixture_text_observation(payload, **common)
    return fixture_binary_observation(payload.encode("utf-8"), **common)


@pytest.mark.parametrize(
    ("first_kind", "second_kind"),
    (
        (ObservationKind.TEXT, ObservationKind.IMAGE),
        (ObservationKind.TRANSCRIPT, ObservationKind.SCREEN),
        (ObservationKind.IMAGE, ObservationKind.TEXT),
        (ObservationKind.SCREEN, ObservationKind.TRANSCRIPT),
    ),
)
def test_equal_content_hash_across_modalities_is_ambiguous(
    first_kind, second_kind,
):
    before = _fixture(first_kind, "shared-synthetic", 100)
    after = _fixture(second_kind, "shared-synthetic", 101, before.content_sha256)
    assert before.content_sha256 == after.content_sha256
    assert before.observation_id != after.observation_id
    with pytest.raises(
        ObservationFixtureChainRejected, match="repeats a content digest",
    ):
        review_disconnected_fixture_chain(
            (before, after), source_id=_SOURCE, privacy_scope=_SCOPE,
        )


@pytest.mark.parametrize(
    ("first_kind", "second_kind"),
    (
        (ObservationKind.TEXT, ObservationKind.IMAGE),
        (ObservationKind.SCREEN, ObservationKind.TRANSCRIPT),
    ),
)
def test_distinct_mixed_modality_fixtures_are_digest_only_and_denied(
    first_kind, second_kind,
):
    first_secret = "first-synthetic-private-payload"
    second_secret = "second-synthetic-private-payload"
    before = _fixture(first_kind, first_secret, 100)
    after = _fixture(second_kind, second_secret, 101, before.content_sha256)
    result = review_disconnected_fixture_chain(
        (before, after), source_id=_SOURCE, privacy_scope=_SCOPE,
    )
    assert result.envelope_count == 2
    assert result.first_observation_id == before.observation_id
    assert result.last_observation_id == after.observation_id
    assert result == review_disconnected_fixture_chain(
        (before, after), source_id=_SOURCE, privacy_scope=_SCOPE,
    )
    assert first_secret not in repr(result)
    assert second_secret not in repr(result)
    assert first_secret not in repr(before)
    assert second_secret not in repr(after)
    assert result.source_authenticated is False
    assert result.consent_verified is False
    assert result.dispatch_authorized is False
