"""Run962: disconnected fixture rejects Unicode metadata display spoofing.

The public frozen ObservationEnvelope v1 still permits these Unicode labels;
the stricter fixture adapter alone denies them before private payload hashing.
No real capture, filesystem, network, device or live adapter is involved.
"""

from __future__ import annotations

import hashlib

import pytest

from ark.disconnected_observation_fixture import (
    DisconnectedFixtureRejected,
    make_disconnected_fixture,
)
from ark.observations import ObservationEnvelope, ObservationKind


_PAYLOAD = b"SYNTHETIC_PRIVATE_BYTES_NOT_CAPTURED"
_FORMAT_CONTROLS = (
    "\u0085", "\u061c", "\u200e", "\u200f",
    "\u2028", "\u2029", "\u202a", "\u202b", "\u202c",
    "\u202d", "\u202e", "\u2066", "\u2067", "\u2068", "\u2069",
)


@pytest.mark.parametrize("control", _FORMAT_CONTROLS)
@pytest.mark.parametrize("field", ("source_id", "privacy_scope"))
def test_fixture_refuses_spoofed_labels_without_changing_frozen_envelope(
    control: str, field: str,
) -> None:
    fields = {
        "kind": ObservationKind.TEXT,
        "source_id": "synthetic-source",
        "privacy_scope": "private-fixture",
        "ingested_at_ms": 99,
        "payload": _PAYLOAD,
    }
    fields[field] = "left" + control + "right"
    # Direct v1 syntax is intentionally unchanged; the optional fixture
    # boundary is stricter than the shared frozen public data contract.
    direct = ObservationEnvelope(
        kind=fields["kind"],
        source_id=fields["source_id"],
        adapter_id="fixture.direct.v1",
        privacy_scope=fields["privacy_scope"],
        ingested_at_ms=99,
        content_sha256=hashlib.sha256(_PAYLOAD).hexdigest(),
    )
    assert direct.observation_id.startswith("obs_")
    with pytest.raises(DisconnectedFixtureRejected, match="Unicode formatting control"):
        make_disconnected_fixture(**fields)


def test_multilingual_fixture_metadata_without_bidi_controls_stays_usable() -> None:
    envelope = make_disconnected_fixture(
        kind=ObservationKind.TRANSCRIPT,
        source_id="東京/שלום",
        privacy_scope="研究/خصوصية-β",
        ingested_at_ms=123,
        payload=_PAYLOAD,
    )
    assert envelope.content_sha256 == hashlib.sha256(_PAYLOAD).hexdigest()
    assert envelope.adapter_id == "fixture.disconnected.v1"
    assert not hasattr(envelope, "payload")
    assert _PAYLOAD.decode("ascii") not in repr(envelope)
