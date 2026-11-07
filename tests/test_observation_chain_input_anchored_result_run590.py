"""A disconnected observation result must remain bound to validated input.

Fixtures contain only synthetic metadata. Nothing here authenticates a sensor,
user consent, recording time or permission to use an external tool.
"""

import pytest

import ark.observation_fixture_chain_review as module
from ark.observation_fixture_adapters import fixture_text_observation
from ark.observations import ObservationKind


def _chain():
    first = fixture_text_observation(
        "synthetic first", kind=ObservationKind.TRANSCRIPT,
        source_id="offline", privacy_scope="private", ingested_at_ms=10,
    )
    second = fixture_text_observation(
        "synthetic second", kind=ObservationKind.TRANSCRIPT,
        source_id="offline", privacy_scope="private", ingested_at_ms=11,
        parent_sha256=first.content_sha256,
    )
    return (first, second)


def _review():
    return module.review_disconnected_fixture_chain(
        _chain(), source_id="offline", privacy_scope="private",
    )


def _clone(value):
    replacement = ("!" + value)[1:]
    assert replacement == value and replacement is not value
    return replacement


@pytest.mark.parametrize(
    "field",
    (
        "source_id", "privacy_scope", "envelope_count",
        "first_observation_id", "last_observation_id", "chain_sha256",
    ),
)
def test_constructor_cannot_replace_validated_chain_result_carrier(
    monkeypatch, field,
):
    result_type = module.DisconnectedObservationChainReview
    original = result_type.__init__

    def altered(self, *args):
        original(self, *args)
        value = getattr(self, field)
        replacement = value + 1 if field == "envelope_count" else _clone(value)
        object.__setattr__(self, field, replacement)

    monkeypatch.setattr(result_type, "__init__", altered)
    # Original constructor identity is pinned before any caller hook can run.
    with pytest.raises(module.ObservationFixtureChainRejected, match="implementation changed"):
        _review()


def test_ordinary_closed_chain_is_input_bound_and_non_authorizing():
    rows = _chain()
    result = module.review_disconnected_fixture_chain(
        rows, source_id="offline", privacy_scope="private",
    )
    assert result.source_id == rows[0].source_id
    assert result.privacy_scope == rows[0].privacy_scope
    assert result.first_observation_id == rows[0].observation_id
    assert result.last_observation_id == rows[-1].observation_id
    assert result.envelope_count == len(rows)
    assert result.source_authenticated is False
    assert result.consent_verified is False
    assert result.dispatch_authorized is False
