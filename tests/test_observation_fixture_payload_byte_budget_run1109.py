"""Run1109: fixture payload byte limits precede private hashing."""

from __future__ import annotations

import hashlib

import pytest

from ark import observation_fixture_adapters as adapters
from ark.observations import ObservationKind


def _metadata(kind: ObservationKind) -> dict[str, object]:
    return {
        "kind": kind,
        "source_id": "synthetic-local-source",
        "privacy_scope": "private:fixture",
        "ingested_at_ms": 1_234,
    }


@pytest.mark.parametrize(
    ("kind", "payload"),
    (
        (ObservationKind.TEXT, "x" * (4 * 1024 * 1024 + 1)),
        # Character count is below the byte limit; strict UTF-8 encoding
        # expands each scalar to four bytes and must still be bounded.
        (ObservationKind.TRANSCRIPT, "🧪" * (1024 * 1024 + 1)),
        (ObservationKind.IMAGE, b"x" * (4 * 1024 * 1024 + 1)),
        (ObservationKind.SCREEN, b"x" * (4 * 1024 * 1024 + 1)),
    ),
)
def test_over_budget_fixture_is_rejected_before_private_hash(
    monkeypatch, kind: ObservationKind, payload: str | bytes,
) -> None:
    touched: list[object] = []

    def forbidden_hash(value: bytes) -> str:
        touched.append(value)
        raise AssertionError("over-budget private content reached hashing")

    monkeypatch.setattr(adapters, "_hash_private_fixture", forbidden_hash)
    with pytest.raises(ValueError, match="fixture content byte budget exceeded"):
        if kind in (ObservationKind.TEXT, ObservationKind.TRANSCRIPT):
            adapters.fixture_text_observation(
                payload,
                **_metadata(kind),
            )
        else:
            adapters.fixture_binary_observation(
                payload,
                **_metadata(kind),
            )
    assert touched == []


@pytest.mark.parametrize("binary", (False, True))
def test_exact_fixture_byte_budget_remains_accepted_and_digest_only(binary: bool) -> None:
    if binary:
        payload: str | bytes = b"x" * (4 * 1024 * 1024)
        envelope = adapters.fixture_binary_observation(
            payload,
            **_metadata(ObservationKind.IMAGE),
        )
        digest_input = payload
    else:
        payload = "x" * (4 * 1024 * 1024)
        envelope = adapters.fixture_text_observation(
            payload,
            **_metadata(ObservationKind.TEXT),
        )
        digest_input = payload.encode("utf-8")

    assert envelope.content_sha256 == hashlib.sha256(digest_input).hexdigest()
    assert envelope.schema_version == 1
    assert not hasattr(envelope, "raw_bytes")
    assert not hasattr(envelope, "payload")
