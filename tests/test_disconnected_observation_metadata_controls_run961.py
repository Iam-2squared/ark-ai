"""Run961: disconnected observation adapter rejects ambiguous metadata controls.

This is an opt-in fixture admission guard. The frozen ObservationEnvelope
contract stays unchanged; all payloads are synthetic in-memory bytes, with no
camera, microphone, filesystem, network or execution adapter invoked.
"""

from __future__ import annotations

import hashlib

import pytest

from ark.disconnected_observation_fixture import (
    DisconnectedFixtureRejected,
    make_disconnected_fixture,
)
from ark.observations import ObservationEnvelope, ObservationKind

_PAYLOAD = b"PRIVATE_SYNTHETIC_OBSERVATION_NO_CAPTURE"


@pytest.mark.parametrize("control", ("\n", "\r", "\t", "\x01", "\x1f", "\x7f"))
@pytest.mark.parametrize("field", ("source_id", "privacy_scope"))
def test_opt_in_fixture_rejects_controls_before_private_payload_hash(
    control: str, field: str,
) -> None:
    fields = {
        "kind": ObservationKind.TEXT,
        "source_id": "synthetic-source",
        "privacy_scope": "private-synthetic",
        "ingested_at_ms": 123,
        "payload": _PAYLOAD,
    }
    fields[field] = "left" + control + "right"

    # Direct ObservationEnvelope v1 still permits this metadata spelling;
    # tightening its public/frozen contract is explicitly out of scope.
    direct = ObservationEnvelope(
        kind=fields["kind"],
        source_id=fields["source_id"],
        adapter_id="fixture.direct.v1",
        privacy_scope=fields["privacy_scope"],
        ingested_at_ms=123,
        content_sha256=hashlib.sha256(_PAYLOAD).hexdigest(),
    )
    assert direct.observation_id.startswith("obs_")

    with pytest.raises(DisconnectedFixtureRejected, match="control delimiter"):
        make_disconnected_fixture(**fields)


def test_unicode_fixture_metadata_remains_content_minimizing_and_deny_only() -> None:
    envelope = make_disconnected_fixture(
        kind=ObservationKind.TRANSCRIPT,
        source_id="synthetic-東京",
        privacy_scope="private/研究-β",
        ingested_at_ms=42,
        payload=_PAYLOAD,
    )
    assert envelope.content_sha256 == hashlib.sha256(_PAYLOAD).hexdigest()
    assert envelope.observation_id.startswith("obs_")
    assert envelope.adapter_id == "fixture.disconnected.v1"
    assert not hasattr(envelope, "payload")
    assert _PAYLOAD.decode("ascii") not in repr(envelope)
