"""Closed, disconnected observation reviews reject altered carriers before field reads.

No fixture touches an input device, network, ToolBackend or durable Memory.
Tests never replace the __new__ method on an existing Python type.
"""

import pytest

import ark.observation_fixture_chain_review as chain
from ark.observation_fixture_adapters import fixture_text_observation
from ark.observations import ObservationEnvelope, ObservationKind


def _fixture():
    return fixture_text_observation(
        "synthetic note", kind=ObservationKind.TEXT,
        source_id="fixture", privacy_scope="local:private",
        ingested_at_ms=7,
    )


@pytest.mark.parametrize(
    "mutation",
    ["kind", "source_id", "privacy_scope", "content_sha256",
     "post_init", "getattribute", "getattr"],
)
def test_input_carrier_tampering_rejected_before_private_read(
    monkeypatch, mutation,
):
    row = _fixture()

    def rogue(*_args, **_kwargs):
        pytest.fail("untrusted envelope callback must not execute")

    if mutation == "post_init":
        monkeypatch.setattr(ObservationEnvelope, "__post_init__", rogue)
    elif mutation == "getattribute":
        monkeypatch.setattr(
            ObservationEnvelope, "__getattribute__", rogue,
        )
    elif mutation == "getattr":
        monkeypatch.setattr(
            ObservationEnvelope, "__getattr__", rogue, raising=False,
        )
    else:
        monkeypatch.setattr(ObservationEnvelope, mutation, property(rogue))

    with pytest.raises(chain.ObservationFixtureChainRejected, match="implementation"):
        chain.review_disconnected_fixture_chain(
            (row,), source_id="fixture", privacy_scope="local:private",
        )


@pytest.mark.parametrize(
    "mutation",
    ["exported", "initializer", "source_id", "chain_sha256",
     "getattribute", "getattr", "consent_verified"],
)
def test_result_carrier_tampering_rejected_before_envelope_read(
    monkeypatch, mutation,
):
    row = _fixture()
    review = chain.DisconnectedObservationChainReview

    def rogue(*_args, **_kwargs):
        pytest.fail("untrusted result callback must not execute")

    if mutation == "exported":
        monkeypatch.setattr(chain, "DisconnectedObservationChainReview", object)
    elif mutation == "initializer":
        monkeypatch.setattr(review, "__init__", rogue)
    elif mutation == "getattribute":
        monkeypatch.setattr(review, "__getattribute__", rogue)
    elif mutation == "getattr":
        monkeypatch.setattr(review, "__getattr__", rogue, raising=False)
    else:
        monkeypatch.setattr(review, mutation, property(rogue))

    with pytest.raises(chain.ObservationFixtureChainRejected, match="implementation"):
        chain.review_disconnected_fixture_chain(
            (row,), source_id="fixture", privacy_scope="local:private",
        )


def test_intact_fixture_review_stays_deny_only_and_deterministic():
    row = _fixture()
    first = chain.review_disconnected_fixture_chain(
        (row,), source_id="fixture", privacy_scope="local:private",
    )
    second = chain.review_disconnected_fixture_chain(
        (row,), source_id="fixture", privacy_scope="local:private",
    )
    assert first == second
    assert first.envelope_count == 1
    assert first.source_authenticated is False
    assert first.consent_verified is False
    assert first.dispatch_authorized is False
