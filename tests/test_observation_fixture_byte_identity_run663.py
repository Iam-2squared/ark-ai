"""Offline observation fixtures preserve byte identity without storing media.

All inputs are synthetic, in memory, and unconnected to cameras, microphones,
network or tool dispatch. Digest equality is not provenance or consent.
"""

from __future__ import annotations

import hashlib

import pytest

from ark.observation_fixture_adapters import (
    fixture_binary_observation,
    fixture_text_observation,
)
from ark.observations import ObservationKind


def _text(content, **changes):
    return fixture_text_observation(
        content,
        kind=ObservationKind.TRANSCRIPT,
        source_id="disconnected-mock",
        privacy_scope="fixture:private",
        ingested_at_ms=10,
        **changes,
    )


def test_unicode_equivalent_text_keeps_exact_bytes_not_normalized():
    composed = _text("\u00e9")
    decomposed = _text("e\u0301")
    assert composed.content_sha256 == hashlib.sha256("\u00e9".encode()).hexdigest()
    assert decomposed.content_sha256 == hashlib.sha256("e\u0301".encode()).hexdigest()
    assert composed.content_sha256 != decomposed.content_sha256
    assert composed.observation_id != decomposed.observation_id
    assert "e\u0301" not in repr(decomposed)
    assert not hasattr(composed, "content")
    assert not hasattr(composed, "payload")


def test_parent_link_does_not_change_raw_content_digest():
    first = _text("synthetic")
    child = fixture_text_observation(
        "synthetic", kind=ObservationKind.TRANSCRIPT,
        source_id="disconnected-mock", privacy_scope="fixture:private",
        ingested_at_ms=10, parent_sha256=first.content_sha256,
    )
    assert child.content_sha256 == first.content_sha256
    assert child.observation_id != first.observation_id
    assert child.parent_sha256 == first.content_sha256


@pytest.mark.parametrize("kind", (ObservationKind.IMAGE, ObservationKind.SCREEN))
def test_binary_including_zero_bytes_is_content_bound_not_retained(kind):
    original = b"\x00\xff\x00"
    changed = b"\x00\xfe\x00"
    args = dict(
        kind=kind, source_id="fixture-media",
        privacy_scope="fixture:private", ingested_at_ms=10,
    )
    left = fixture_binary_observation(original, **args)
    right = fixture_binary_observation(changed, **args)
    assert left.content_sha256 == hashlib.sha256(original).hexdigest()
    assert left.content_sha256 != right.content_sha256
    assert left.observation_id != right.observation_id
    assert not hasattr(left, "payload")
    assert not hasattr(left, "raw_bytes")


def test_unpaired_utf16_surrogate_fails_before_any_envelope_is_built():
    with pytest.raises(ValueError, match="not valid UTF-8"):
        _text("\ud800")


def test_utf8_byte_limit_rejects_multibyte_under_character_limit():
    # The character count fits, but the encoded bytes exceed 4 MiB.
    over_bytes = "\u00e9" * (2 * 1024 * 1024 + 1)
    assert len(over_bytes) < 4 * 1024 * 1024
    with pytest.raises(ValueError, match="byte budget exceeded"):
        _text(over_bytes)
