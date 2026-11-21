"""Hash disconnected synthetic bytes with the import-pinned implementation.

The reentrant swap is a local fault-injection fixture, not an actual attack
or proof that a compromised Python process can be trusted.
"""

from __future__ import annotations

import hashlib

import pytest

from ark import disconnected_observation_fixture as fixture
from ark.observations import ObservationKind


def test_reentrant_hash_substitution_cannot_receive_private_fixture(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    original_guard = fixture._require_fixture_boundary
    guard_calls = 0
    leaked: list[object] = []

    def hostile_hash(data: object) -> object:
        leaked.append(data)
        pytest.fail("raw synthetic fixture reached substituted digest")

    def interleaved_guard() -> None:
        nonlocal guard_calls
        original_guard()
        guard_calls += 1
        # The second guard is after envelope preflight but before hashing.
        if guard_calls == 2:
            monkeypatch.setattr(fixture.hashlib, "sha256", hostile_hash)

    monkeypatch.setattr(fixture, "_require_fixture_boundary", interleaved_guard)
    with pytest.raises(fixture.DisconnectedFixtureRejected, match="boundary changed"):
        fixture.make_disconnected_fixture(
            kind=ObservationKind.IMAGE,
            source_id="synthetic-device",
            privacy_scope="synthetic-private",
            ingested_at_ms=10,
            payload=b"synthetic-private-bytes",
        )
    assert guard_calls == 2
    assert leaked == []


def test_valid_disconnected_hash_has_no_payload_in_result() -> None:
    payload = b"synthetic-observation-fixture"
    envelope = fixture.make_disconnected_fixture(
        kind=ObservationKind.TRANSCRIPT,
        source_id="synthetic-source",
        privacy_scope="local-fixture",
        ingested_at_ms=42,
        payload=payload,
        parent_sha256="a" * 64,
    )
    assert envelope.content_sha256 == hashlib.sha256(payload).hexdigest()
    assert envelope.parent_sha256 == "a" * 64
    assert payload.decode("ascii") not in repr(envelope)
