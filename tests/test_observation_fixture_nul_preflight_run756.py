"""Reject ambiguous observation fixture labels before private hashing.

No sensor capture, file I/O, media retention, or external action is used.
"""

from __future__ import annotations

import hashlib

import pytest

from ark import observation_fixture_adapters as adapters
from ark.observations import ObservationKind


@pytest.mark.parametrize("adapter", ("text", "binary"))
@pytest.mark.parametrize("label", ("source_id", "privacy_scope"))
@pytest.mark.parametrize("value", ("a\x00b", "\x00leading", "trailing\x00"))
def test_nul_fixture_metadata_never_reaches_raw_content_hash(
    monkeypatch, adapter, label, value,
):
    calls = []

    def forbidden(payload):
        calls.append(payload)
        raise AssertionError("private fixture reached hash after invalid label")

    monkeypatch.setattr(adapters, "_hash_private_fixture", forbidden)
    kwargs = {
        "source_id": "local:synthetic",
        "privacy_scope": "local:private",
        "ingested_at_ms": 23,
    }
    kwargs[label] = value
    with pytest.raises(ValueError, match="NUL separator"):
        if adapter == "text":
            adapters.fixture_text_observation(
                "private synthetic text", kind=ObservationKind.TEXT, **kwargs,
            )
        else:
            adapters.fixture_binary_observation(
                b"private synthetic bytes", kind=ObservationKind.IMAGE, **kwargs,
            )
    assert calls == []


def test_clean_observation_fixture_still_returns_only_digest_metadata():
    text = adapters.fixture_text_observation(
        "synthetic", kind=ObservationKind.TRANSCRIPT,
        source_id="local:synthetic", privacy_scope="local:private",
        ingested_at_ms=23,
    )
    binary = adapters.fixture_binary_observation(
        b"synthetic", kind=ObservationKind.SCREEN,
        source_id="local:synthetic", privacy_scope="local:private",
        ingested_at_ms=23,
    )
    assert text.content_sha256 == binary.content_sha256
    assert text.content_sha256 == hashlib.sha256(b"synthetic").hexdigest()
    assert text.observation_id != binary.observation_id
    for observed in (text, binary):
        assert not hasattr(observed, "raw_bytes")
        assert not hasattr(observed, "text")
        assert not hasattr(observed, "external_action_authorized")
