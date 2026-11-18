"""Run971: optional fixture adapter excludes C1 log/terminal delimiters.

The frozen ObservationEnvelope v1 remains untouched; fixtures do not access
devices, store media or confer consent, source authenticity or dispatch.
"""

from __future__ import annotations

import hashlib

import pytest

from ark.disconnected_observation_fixture import (
    DisconnectedFixtureRejected,
    make_disconnected_fixture,
)
from ark.observations import ObservationEnvelope, ObservationKind

_C1 = ("\u0080", "\u0081", "\u008d", "\u0090", "\u009b", "\u009f")


@pytest.mark.parametrize("control", _C1)
@pytest.mark.parametrize("field", ("source_id", "privacy_scope"))
def test_c1_fixture_label_denied_without_returned_envelope(
    control: str, field: str,
) -> None:
    labels = {"source_id": "synthetic/sensor", "privacy_scope": "local-private"}
    labels[field] += control + "forged"
    with pytest.raises(DisconnectedFixtureRejected, match="Unicode formatting control"):
        make_disconnected_fixture(
            kind=ObservationKind.TEXT,
            source_id=labels["source_id"],
            privacy_scope=labels["privacy_scope"],
            ingested_at_ms=100,
            payload=b"synthetic-only",
        )


def test_frozen_v1_envelope_semantics_are_not_tightened() -> None:
    # This direct public v1 constructor intentionally has no C1 fixture
    # policy. Strict adapter admission must not silently migrate that contract.
    direct = ObservationEnvelope(
        ObservationKind.TEXT, "sensor\u009bprivate", "mock.adapter",
        "local", 100, "0" * 64,
    )
    assert direct.source_id == "sensor\u009bprivate"
    assert direct.observation_id.startswith("obs_")


def test_accepted_multilingual_fixture_remains_deterministic_and_inert() -> None:
    payload = b"synthetic-payload"
    args = {
        "kind": ObservationKind.TEXT,
        "source_id": "東京/観測",
        "privacy_scope": "ローカルのみ",
        "ingested_at_ms": 100,
        "payload": payload,
    }
    first = make_disconnected_fixture(**args)
    second = make_disconnected_fixture(**args)
    assert first == second
    assert first.content_sha256 == hashlib.sha256(payload).hexdigest()
    assert first.observation_id == second.observation_id
    assert first.adapter_id == "fixture.disconnected.v1"
