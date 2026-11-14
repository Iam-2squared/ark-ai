"""Closed offline observation evidence stays bounded and chronology-sensitive.

Exercise source-independent digest-only chains at both the single-envelope
and maximum fixture count. Missing/altered parents near the end of a long
chain cannot be hidden behind fresh timestamps. No media capture or consent.
"""

from __future__ import annotations

import pytest

from ark.observation_fixture_chain_review import (
    ObservationFixtureChainRejected,
    review_disconnected_fixture_chain,
)
from ark.observations import ObservationEnvelope, ObservationKind


def _chain(length):
    rows = []
    parent = None
    for i in range(1, length + 1):
        digest = f"{i:064x}"
        row = ObservationEnvelope(
            ObservationKind.TEXT, "synthetic-source", "text-fixture",
            "scope:private", 100 + i, digest, parent,
        )
        rows.append(row)
        parent = digest
    return tuple(rows)


def _review(rows):
    return review_disconnected_fixture_chain(
        rows, source_id="synthetic-source", privacy_scope="scope:private",
    )


@pytest.mark.parametrize("length", (1, 16, 64, 256))
def test_closed_chain_count_boundary_is_deterministic_and_non_authorizing(length):
    rows = _chain(length)
    result = _review(rows)
    assert result == _review(rows)
    assert result.envelope_count == length
    assert result.first_observation_id == rows[0].observation_id
    assert result.last_observation_id == rows[-1].observation_id
    assert len(result.chain_sha256) == 64
    assert result.source_authenticated is False
    assert result.consent_verified is False
    assert result.dispatch_authorized is False


def test_257_envelopes_refused_before_any_private_fixture_inspection():
    with pytest.raises(ObservationFixtureChainRejected, match="bounded"):
        _review(_chain(257))


@pytest.mark.parametrize("position", (0, 128, 255))
def test_long_chain_rejects_invalid_parent_at_any_depth(position):
    rows = list(_chain(256))
    earlier = rows[position]
    rows[position] = ObservationEnvelope(
        earlier.kind, earlier.source_id, earlier.adapter_id,
        earlier.privacy_scope, earlier.ingested_at_ms,
        earlier.content_sha256, "f" * 64,
    )
    with pytest.raises(ObservationFixtureChainRejected):
        _review(tuple(rows))
