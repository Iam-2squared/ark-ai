"""Content-minimized Observation fixture identity and privacy metamorphisms.

In-memory synthetic bytes only. No camera, microphone, image decoding, real
observation, private export, trusted clock, or consent is involved.
"""

from __future__ import annotations

import hashlib

import pytest

from ark.disconnected_observation_fixture import (
    DisconnectedFixtureRejected,
    make_disconnected_fixture,
)
from ark.observations import ObservationEnvelope, ObservationKind


@pytest.mark.parametrize(
    ("change", "value"),
    (
        ("kind", ObservationKind.IMAGE),
        ("source_id", "fixture-source-2"),
        ("privacy_scope", "fixture-restricted"),
        ("ingested_at_ms", 101),
        ("parent_sha256", "b" * 64),
    ),
)
def test_same_synthetic_payload_does_not_collapse_identity_across_metadata(
    change: str, value: object,
) -> None:
    fixture = {
        "kind": ObservationKind.TEXT,
        "source_id": "fixture-source-1",
        "privacy_scope": "fixture-local",
        "ingested_at_ms": 100,
        "payload": b"synthetic-sensitive-fixture\x00",
    }
    a = make_disconnected_fixture(**fixture)
    b = make_disconnected_fixture(**{**fixture, change: value})
    original_digest = hashlib.sha256(fixture["payload"]).hexdigest()
    assert a.content_sha256 == original_digest
    assert b.content_sha256 == original_digest
    assert a.observation_id != b.observation_id
    assert a.schema_version == b.schema_version == 1
    assert not hasattr(a, "payload")
    assert "synthetic-sensitive-fixture" not in repr(a)
    assert "synthetic-sensitive-fixture" not in repr(b)


@pytest.mark.parametrize("payload", (b"", b"X" * 65_537, bytearray(b"private")))
def test_disconnected_fixture_rejects_unbounded_or_mutable_input(payload) -> None:
    with pytest.raises(DisconnectedFixtureRejected):
        make_disconnected_fixture(
            kind=ObservationKind.TEXT,
            source_id="fixture-source",
            privacy_scope="fixture-private",
            ingested_at_ms=1,
            payload=payload,
        )


def test_disconnected_fixture_never_calls_user_defined_bytes_conversion() -> None:
    class HostileBytes:
        calls = 0

        def __bytes__(self):
            self.calls += 1
            raise AssertionError("untrusted bytes callback must not run")

    hostile = HostileBytes()
    with pytest.raises(DisconnectedFixtureRejected):
        make_disconnected_fixture(
            kind=ObservationKind.TEXT,
            source_id="fixture-source",
            privacy_scope="fixture-private",
            ingested_at_ms=1,
            payload=hostile,
        )
    assert hostile.calls == 0


def test_adapter_nul_veto_does_not_mutate_direct_v1_envelope_contract() -> None:
    direct = ObservationEnvelope(
        kind=ObservationKind.TEXT,
        source_id="direct\x00fixture",
        adapter_id="direct.v1",
        privacy_scope="private",
        ingested_at_ms=1,
        content_sha256="0" * 64,
    )
    assert direct.observation_id.startswith("obs_")
    with pytest.raises(DisconnectedFixtureRejected, match="NUL"):
        make_disconnected_fixture(
            kind=ObservationKind.TEXT,
            source_id="direct\x00fixture",
            privacy_scope="private",
            ingested_at_ms=1,
            payload=b"fixture",
        )
