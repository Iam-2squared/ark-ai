"""A disconnected observation chain refuses hash/domain substitution pre-review.

Digest-only fixture lineage cannot authenticate a camera/microphone, user
consent, data retention, external disclosure, or execution capability.
"""

from __future__ import annotations

import pytest

import ark.observation_fixture_chain_review as chain
from ark.observation_fixture_adapters import fixture_text_observation
from ark.observations import ObservationKind


@pytest.mark.parametrize(
    "substitution",
    ("hashlib_module", "sha256", "domain", "equal_domain_object"),
)
def test_digest_implementation_epoch_rejected_before_observation_inspection(
    monkeypatch, substitution,
):
    first = fixture_text_observation(
        "local private root", kind=ObservationKind.TEXT,
        source_id="offline", privacy_scope="private", ingested_at_ms=10,
    )
    second = fixture_text_observation(
        "local derived text", kind=ObservationKind.TRANSCRIPT,
        source_id="offline", privacy_scope="private", ingested_at_ms=11,
        parent_sha256=first.content_sha256,
    )
    calls = []

    def forbidden(*args, **kwargs):
        calls.append((args, kwargs))
        raise AssertionError("untrusted hash implementation was invoked")

    with monkeypatch.context() as patch:
        if substitution == "hashlib_module":
            patch.setattr(chain, "hashlib", object())
        elif substitution == "sha256":
            patch.setattr(chain.hashlib, "sha256", forbidden)
        elif substitution == "domain":
            patch.setattr(chain, "_DOMAIN", b"not-original-chain-domain")
        else:
            same = bytes(bytearray(chain._DOMAIN))
            assert same == chain._DOMAIN
            assert same is not chain._DOMAIN
            patch.setattr(chain, "_DOMAIN", same)
        with pytest.raises(
            chain.ObservationFixtureChainRejected,
            match="digest implementation changed",
        ):
            chain.review_disconnected_fixture_chain(
                (first, second), source_id="offline", privacy_scope="private",
            )

    assert calls == []
    result = chain.review_disconnected_fixture_chain(
        (first, second), source_id="offline", privacy_scope="private",
    )
    assert result.envelope_count == 2
    assert result.source_authenticated is False
    assert result.consent_verified is False
    assert result.dispatch_authorized is False
    assert not hasattr(result, "raw_media")
