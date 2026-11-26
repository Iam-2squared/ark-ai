"""Synthetic-only observation adapter: bounded and content-minimized.

All inputs are generated in memory. No camera, microphone, screen, file,
network adapter, real provenance or external backend is involved.
"""

import hashlib

import pytest

from ark import disconnected_observation_fixture as fixture
from ark import observations


@pytest.mark.parametrize("kind", tuple(observations.ObservationKind))
def test_each_modality_has_an_inert_content_minimized_envelope(
    kind: observations.ObservationKind,
) -> None:
    payload = b"synthetic local fixture only"
    envelope = fixture.make_disconnected_fixture(
        kind=kind, source_id="sample", privacy_scope="private-test",
        ingested_at_ms=10, payload=payload,
    )
    assert type(envelope) is observations.ObservationEnvelope
    assert envelope.kind is kind
    assert envelope.content_sha256 == hashlib.sha256(payload).hexdigest()
    assert envelope.adapter_id == "fixture.disconnected.v1"
    assert envelope.observation_id.startswith("obs_")
    assert payload.decode("ascii") not in repr(envelope)
    assert not hasattr(envelope, "payload")


@pytest.mark.parametrize("size", (0, 65_537, 131_072))
def test_nonadmitted_payload_has_no_hash_or_envelope_side_effect(
    monkeypatch: pytest.MonkeyPatch, size: int,
) -> None:
    # For invalid inputs, admission must reject before even a digest attempt.
    # The function is intentionally *not* patched here: the adapter pins its
    # hashing dependencies. Compare the resulting exception instead.
    with pytest.raises(fixture.DisconnectedFixtureRejected, match="exact bytes"):
        fixture.make_disconnected_fixture(
            kind=observations.ObservationKind.TEXT,
            source_id="sample", privacy_scope="private-test",
            ingested_at_ms=0, payload=b"x" * size,
        )


def test_exact_payload_budget_remains_accepted() -> None:
    envelope = fixture.make_disconnected_fixture(
        kind=observations.ObservationKind.IMAGE,
        source_id="test-image", privacy_scope="private-test",
        ingested_at_ms=0, payload=b"z" * 65_536,
    )
    assert len(envelope.content_sha256) == 64


@pytest.mark.parametrize("payload", (bytearray(b"image"), memoryview(b"image"), "image"))
def test_mutable_or_coercible_buffer_is_not_accepted(payload: object) -> None:
    with pytest.raises(fixture.DisconnectedFixtureRejected, match="exact bytes"):
        fixture.make_disconnected_fixture(
            kind=observations.ObservationKind.SCREEN,
            source_id="source", privacy_scope="private-test",
            ingested_at_ms=0, payload=payload,  # type: ignore[arg-type]
        )


def test_digest_substitution_is_refused_before_private_bytes_reach_callback(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    received: list[object] = []

    def replaced_sha256(value: object) -> object:
        received.append(value)
        raise AssertionError("fixture bytes reached substituted digest")

    monkeypatch.setattr(fixture.hashlib, "sha256", replaced_sha256)
    with pytest.raises(fixture.DisconnectedFixtureRejected, match="boundary changed"):
        fixture.make_disconnected_fixture(
            kind=observations.ObservationKind.TRANSCRIPT,
            source_id="source", privacy_scope="private-test",
            ingested_at_ms=0, payload=b"do not release",
        )
    assert received == []


def test_replaced_observation_constructor_is_refused(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(observations, "ObservationEnvelope", object)
    with pytest.raises(fixture.DisconnectedFixtureRejected, match="boundary changed"):
        fixture.make_disconnected_fixture(
            kind=observations.ObservationKind.TEXT,
            source_id="source", privacy_scope="private-test",
            ingested_at_ms=0, payload=b"synthetic",
        )


def test_invalid_privacy_label_still_fails_closed() -> None:
    with pytest.raises(ValueError, match="observation identifier budget"):
        fixture.make_disconnected_fixture(
            kind=observations.ObservationKind.TEXT,
            source_id="source", privacy_scope="x" * 1025,
            ingested_at_ms=0, payload=b"synthetic",
        )
