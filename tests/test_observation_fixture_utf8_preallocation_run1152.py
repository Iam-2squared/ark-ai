"""Run1152: bound temporary UTF-8 encoding for private observation fixtures."""

from __future__ import annotations

import pytest

from ark import observation_fixture_adapters as adapters
from ark.observations import ObservationKind


def test_bounded_encoder_preserves_ascii_and_multibyte_exact_boundaries() -> None:
    assert adapters._encode_fixture_text_bounded("ascii", 5) == b"ascii"
    assert adapters._encode_fixture_text_bounded("🧪🧪", 8) == "🧪🧪".encode()
    assert adapters._encode_fixture_text_bounded("🧪🧪🧪", 8) is None


def test_bounded_encoder_stops_on_oversize_multibyte_text() -> None:
    # The full string is caller-owned. The adapter must not build a second
    # full-size UTF-8 byte string just to discover that it exceeds this limit.
    assert adapters._encode_fixture_text_bounded("🧪" * 100_000, 8) is None


def test_bounded_encoder_keeps_strict_surrogate_rejection() -> None:
    with pytest.raises(UnicodeEncodeError):
        adapters._encode_fixture_text_bounded("valid\ud800invalid", 64)


def test_text_fixture_translates_invalid_utf8_before_private_hash(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    touched: list[bytes] = []

    def forbidden_hash(payload: bytes) -> str:
        touched.append(payload)
        raise AssertionError("invalid fixture text reached private hashing")

    monkeypatch.setattr(adapters, "_hash_private_fixture", forbidden_hash)
    with pytest.raises(ValueError, match="fixture text is not valid UTF-8"):
        adapters.fixture_text_observation(
            "synthetic\ud800private",
            kind=ObservationKind.TEXT,
            source_id="synthetic-source",
            privacy_scope="private:fixture",
            ingested_at_ms=1234,
        )
    assert touched == []
