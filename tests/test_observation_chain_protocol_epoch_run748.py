"""Run748: closed observation fixture protocol must be fixed before review.

This is an offline-only metadata fixture, never authenticated observation or
permission to access media, tools or any external service.
"""

from __future__ import annotations

import pytest

import ark.observation_fixture_chain_review as chain
from ark.observation_fixture_adapters import fixture_text_observation
from ark.observations import ObservationKind


def _fixture():
    return fixture_text_observation(
        "synthetic locally held text",
        kind=ObservationKind.TEXT,
        source_id="fixture",
        privacy_scope="local:private",
        ingested_at_ms=123,
    )


def _review(item):
    return chain.review_disconnected_fixture_chain(
        (item,), source_id="fixture", privacy_scope="local:private",
    )


@pytest.mark.parametrize(("name", "replacement"), (
    ("_MAX_ENVELOPES", 257),
    ("_MAX_ENVELOPES", 256.0),
    ("_ENVELOPE_FIELDS", tuple(reversed(chain._ENVELOPE_FIELDS))),
    ("_ENVELOPE_FIELDS", tuple(list(chain._ENVELOPE_FIELDS))),
    ("_HOOKS", tuple(reversed(chain._HOOKS))),
    ("_RESULT_FIELDS", tuple(reversed(chain._RESULT_FIELDS))),
    ("_DENIALS", tuple(reversed(chain._DENIALS))),
))
def test_mutable_protocol_cannot_redefine_private_fixture_admission(
    monkeypatch, name, replacement,
):
    item = _fixture()
    monkeypatch.setattr(chain, name, replacement)
    with pytest.raises(
        chain.ObservationFixtureChainRejected,
        match="digest implementation changed",
    ):
        _review(item)


def test_original_closed_chain_has_no_authority():
    result = _review(_fixture())
    assert result.envelope_count == 1
    assert len(result.chain_sha256) == 64
    assert result.source_authenticated is False
    assert result.consent_verified is False
    assert result.dispatch_authorized is False
