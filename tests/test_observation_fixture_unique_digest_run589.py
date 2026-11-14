"""Closed observation fixture chains require unambiguous parent digests.

Synthetic in-memory observations do not authenticate capture, consent or
external media provenance.
"""

import pytest

from ark.observation_fixture_adapters import fixture_text_observation
from ark.observation_fixture_chain_review import (
    ObservationFixtureChainRejected,
    review_disconnected_fixture_chain,
)
from ark.observations import ObservationKind


def _item(text: str, at: int, parent: str | None = None):
    return fixture_text_observation(
        text,
        kind=ObservationKind.TRANSCRIPT,
        source_id="fixture",
        privacy_scope="local:private",
        ingested_at_ms=at,
        parent_sha256=parent,
    )


def _review(*rows):
    return review_disconnected_fixture_chain(
        tuple(rows), source_id="fixture", privacy_scope="local:private",
    )


def test_adjacent_duplicate_content_is_not_a_closed_chain():
    first = _item("same private text", 10)
    second = _item("same private text", 11, first.content_sha256)
    assert second.parent_sha256 == second.content_sha256
    with pytest.raises(ObservationFixtureChainRejected, match="repeats a content digest"):
        _review(first, second)


def test_nonadjacent_duplicate_content_is_ambiguous():
    first = _item("first private text", 10)
    middle = _item("middle private text", 11, first.content_sha256)
    last = _item("first private text", 12, middle.content_sha256)
    assert last.content_sha256 == first.content_sha256
    with pytest.raises(ObservationFixtureChainRejected, match="repeats a content digest"):
        _review(first, middle, last)


def test_distinct_three_step_fixture_chain_remains_inert():
    first = _item("first private text", 10)
    middle = _item("middle private text", 11, first.content_sha256)
    last = _item("last private text", 12, middle.content_sha256)
    result = _review(first, middle, last)
    assert result.envelope_count == 3
    assert result.first_observation_id == first.observation_id
    assert result.last_observation_id == last.observation_id
    assert result.source_authenticated is False
    assert result.consent_verified is False
    assert result.dispatch_authorized is False
    assert "private text" not in repr(result)
