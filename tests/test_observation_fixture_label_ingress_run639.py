"""Closed fixture chains reject invalid caller labels before envelope reads.

Only synthetic text envelopes are used; no media device or external action.
"""

import pytest

import ark.observation_fixture_chain_review as chain
from ark.observation_fixture_adapters import fixture_text_observation
from ark.observations import ObservationKind


@pytest.mark.parametrize(
    ("source_id", "privacy_scope", "diagnostic"),
    [
        ("\\ud800", "local:private", "valid UTF-8"),
        ("fixture", "\\udfff", "valid UTF-8"),
        ("s" * 1025, "local:private", "exact bounded"),
        ("fixture", "s" * 1025, "exact bounded"),
        (" ", "local:private", "exact bounded"),
        ("fixture", " ", "exact bounded"),
    ],
)
def test_bad_fixture_labels_fail_before_reading_envelope(
    tmp_path, monkeypatch, source_id, privacy_scope, diagnostic,
):
    del tmp_path
    envelope = fixture_text_observation(
        "synthetic private note", kind=ObservationKind.TEXT,
        source_id="fixture", privacy_scope="local:private",
        ingested_at_ms=10,
    )

    def must_not_validate(*_args, **_kwargs):
        pytest.fail("invalid review labels reached an envelope callback")

    monkeypatch.setattr(chain, "_ORIGINAL_VALIDATE", must_not_validate)
    with pytest.raises(chain.ObservationFixtureChainRejected, match=diagnostic):
        chain.review_disconnected_fixture_chain(
            (envelope,), source_id=source_id, privacy_scope=privacy_scope,
        )


def test_multilingual_utf8_labels_remain_admissible_to_offline_review():
    envelope = fixture_text_observation(
        "synthetic 文字列", kind=ObservationKind.TEXT,
        source_id="日本語", privacy_scope="local:秘密",
        ingested_at_ms=10,
    )
    review = chain.review_disconnected_fixture_chain(
        (envelope,), source_id="日本語", privacy_scope="local:秘密",
    )
    assert review.envelope_count == 1
    assert review.source_authenticated is False
    assert review.consent_verified is False
    assert review.dispatch_authorized is False
