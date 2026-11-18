"""Run967: invisible Unicode identity denial at disconnected fixture edge.

This module passes synthetic bytes only, does not access a real sensor or
change frozen ObservationEnvelope v1, and grants no runtime authorization.
"""

from __future__ import annotations

import hashlib

import pytest

from ark.disconnected_observation_fixture import (
    DisconnectedFixtureRejected,
    make_disconnected_fixture,
)
from ark.observations import ObservationEnvelope, ObservationKind


_INVISIBLE_SCALARS = (
    0x00AD, 0x034F, 0x180E, 0x200B, 0x200C, 0x200D,
    0x2060, 0x2061, 0x2062, 0x2063, 0x2064, 0xFEFF,
    0x206A, 0x206B, 0x206C, 0x206D, 0x206E, 0x206F,
)


@pytest.mark.parametrize("field", ("source_id", "privacy_scope"))
@pytest.mark.parametrize("codepoint", _INVISIBLE_SCALARS)
def test_opt_in_fixture_metadata_rejects_invisible_unicode(field, codepoint):
    values = {
        "kind": ObservationKind.TEXT,
        "source_id": "local:synthetic-source",
        "privacy_scope": "local:private",
        "ingested_at_ms": 42,
        "payload": b"private synthetic bytes only",
    }
    values[field] = "local:" + chr(codepoint) + "synthetic"
    with pytest.raises(
        DisconnectedFixtureRejected, match="Unicode formatting control",
    ):
        make_disconnected_fixture(**values)


@pytest.mark.parametrize("label", (
    "日本語の観測源",
    "e\u0301cole:synthetic",
    "local:研究/安全",
))
def test_normal_unicode_labels_are_still_admitted(label):
    payload = b"synthetic payload for digest-only envelope"
    result = make_disconnected_fixture(
        kind=ObservationKind.TEXT,
        source_id=label,
        privacy_scope="local:private",
        ingested_at_ms=123,
        payload=payload,
    )
    assert result.source_id == label
    assert result.content_sha256 == hashlib.sha256(payload).hexdigest()
    assert not hasattr(result, "payload")
    assert not hasattr(result, "raw_bytes")


def test_public_observation_v1_contract_not_tightened():
    # The additional check belongs only to opt-in disconnected fixture input.
    retained = ObservationEnvelope(
        kind=ObservationKind.TEXT,
        source_id="legacy\u200bsynthetic",
        adapter_id="fixture.disconnected.v1",
        privacy_scope="local:private",
        ingested_at_ms=42,
        content_sha256="0" * 64,
    )
    assert retained.source_id == "legacy\u200bsynthetic"
