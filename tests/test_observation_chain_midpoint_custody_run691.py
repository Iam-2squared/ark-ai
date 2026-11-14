"""Middle-of-chain observation metadata must not launder provenance or identity.

Offline digest-only fixtures never authenticate capture source or consent.
A valid mixed-kind chain stays a purely local non-authorizing diagnostic.
"""

from __future__ import annotations

from dataclasses import replace

import pytest

from ark.observation_fixture_chain_review import (
    ObservationFixtureChainRejected,
    review_disconnected_fixture_chain,
)
from ark.observations import ObservationEnvelope, ObservationKind


def _chain(length):
    rows = []
    parent = None
    for index in range(length):
        digest = f"{index + 1:064x}"
        rows.append(ObservationEnvelope(
            ObservationKind.TEXT, "fixture-source", "offline-text",
            "scope:private", 100 + index, digest, parent,
        ))
        parent = digest
    return tuple(rows)


def _review(rows):
    return review_disconnected_fixture_chain(
        rows, source_id="fixture-source", privacy_scope="scope:private",
    )


@pytest.mark.parametrize(
    "fault",
    (
        "repeated_content_digest",
        "cross_source",
        "cross_privacy_scope",
        "equal_timestamp",
        "regressed_timestamp",
    ),
)
def test_middle_of_closed_chain_rejects_identity_and_time_splicing(fault):
    rows = list(_chain(256))
    current = rows[128]
    previous = rows[127]
    if fault == "repeated_content_digest":
        older_digest = rows[16].content_sha256
        rows[128] = replace(current, content_sha256=older_digest)
        rows[129] = replace(rows[129], parent_sha256=older_digest)
    elif fault == "cross_source":
        rows[128] = replace(current, source_id="other-source")
    elif fault == "cross_privacy_scope":
        rows[128] = replace(current, privacy_scope="scope:other")
    elif fault == "equal_timestamp":
        rows[128] = replace(current, ingested_at_ms=previous.ingested_at_ms)
    elif fault == "regressed_timestamp":
        rows[128] = replace(current, ingested_at_ms=previous.ingested_at_ms - 1)

    with pytest.raises(ObservationFixtureChainRejected):
        _review(tuple(rows))


@pytest.mark.parametrize("length", (2, 8, 24))
def test_valid_mixed_fixture_kind_changes_digest_without_granting_authority(length):
    rows = list(_chain(length))
    original = _review(tuple(rows))
    rows[1] = replace(rows[1], kind=ObservationKind.TRANSCRIPT)
    reviewed = _review(tuple(rows))
    assert reviewed.chain_sha256 != original.chain_sha256
    assert reviewed.envelope_count == length
    assert reviewed.source_authenticated is False
    assert reviewed.consent_verified is False
    assert reviewed.dispatch_authorized is False
