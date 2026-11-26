"""Run965: detached free-only V3 bytes never launder escaped JSON keys.

Synthetic, canonical, in-memory evidence only. No local models, GPU, paid
compute, credentials, protected evaluation, training or Candidate promotion.
"""

from __future__ import annotations

import json

import pytest

from ark.v3_detached_packet_review import (
    DetachedV3PacketRejected,
    review_detached_v3_packet,
)


def _packet(*, seconds: float = 300.0) -> bytes:
    values = {
        "snapshot": {
            "device": "cuda:0",
            "capacity_gib": 12.0,
            "tokenizer_probe_sha256": "a" * 64,
            "wall_clock_timeout_minutes": 20,
        },
        "evidence": {
            "device": "cuda:0",
            "reported_capacity_gib": 12.0,
            "tokenizer_probe_sha256": "a" * 64,
            "peak_vram_mib": 4096.0,
            "peak_reserved_vram_mib": 6144.0,
            "wall_seconds": seconds,
        },
    }
    return json.dumps(
        values, ensure_ascii=True, sort_keys=True,
        separators=(",", ":"), allow_nan=False,
    ).encode("ascii")


@pytest.mark.parametrize("mutation", (
    "escaped-duplicate-root",
    "escaped-duplicate-nested",
    "escaped-canonical-root",
    "scientific-capacity",
    "scientific-vram",
    "scientific-time",
))
def test_equivalent_or_ambiguous_noncanonical_bytes_denied(mutation: str) -> None:
    encoded = _packet()
    if mutation == "escaped-duplicate-root":
        encoded = encoded[:-1] + b',"\\u0073napshot":{}}'
    elif mutation == "escaped-duplicate-nested":
        encoded = encoded.replace(
            b'"device":', b'"\\u0064evice":"cuda:0","device":', 1,
        )
    elif mutation == "escaped-canonical-root":
        encoded = encoded.replace(b'"snapshot":', b'"\\u0073napshot":', 1)
    elif mutation == "scientific-capacity":
        encoded = encoded.replace(b'12.0', b'1.2e1', 1)
    elif mutation == "scientific-vram":
        encoded = encoded.replace(b'4096.0', b'4.096e3', 1)
    else:
        encoded = encoded.replace(b'300.0', b'3e2', 1)
    assert encoded != _packet()
    assert len(encoded) <= 4096
    with pytest.raises(DetachedV3PacketRejected):
        review_detached_v3_packet(encoded)


def test_free_only_packet_digests_bind_exact_evidence_values_without_authority() -> None:
    first = review_detached_v3_packet(_packet(seconds=300.0))
    second = review_detached_v3_packet(_packet(seconds=301.0))
    assert first.packet_sha256 != second.packet_sha256
    assert first.crossbind_digest != second.crossbind_digest
    assert first.checks == second.checks
    for output in (first, second):
        assert output.paid_compute_authorized is False
        assert output.training_authorized is False
        assert output.candidate_promotion_authorized is False
        assert output.provenance_authenticated is False
