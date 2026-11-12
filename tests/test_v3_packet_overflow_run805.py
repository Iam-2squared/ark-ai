"""Exponent-overflow V3 JSON is rejected as a bounded offline packet error.

The fixture cannot authenticate provenance or authorize paid computation,
training, promotion or protected evaluation.
"""

from __future__ import annotations

import json

import pytest

from ark import v3_detached_packet_review as packet_review

_SHA = "a" * 64


def _packet() -> bytes:
    return json.dumps(
        {
            "snapshot": {
                "device": "cuda:0",
                "capacity_gib": 12.0,
                "tokenizer_probe_sha256": _SHA,
                "wall_clock_timeout_minutes": 20,
            },
            "evidence": {
                "device": "cuda:0",
                "reported_capacity_gib": 12.0,
                "tokenizer_probe_sha256": _SHA,
                "peak_vram_mib": 4096.0,
                "peak_reserved_vram_mib": 6144.0,
                "wall_seconds": 300.0,
            },
        },
        ensure_ascii=True, sort_keys=True, separators=(",", ":"),
        allow_nan=False,
    ).encode("ascii")


@pytest.mark.parametrize(
    ("field", "original"),
    (
        ("capacity_gib", "12.0"),
        ("reported_capacity_gib", "12.0"),
        ("peak_vram_mib", "4096.0"),
        ("peak_reserved_vram_mib", "6144.0"),
        ("wall_seconds", "300.0"),
    ),
)
@pytest.mark.parametrize("exponent", (b"1e999", b"-1e999"))
def test_numeric_exponent_overflow_is_classified_as_packet_rejection(
    field: str, original: str, exponent: bytes,
) -> None:
    marker = f'"{field}":{original}'.encode("ascii")
    original_packet = _packet()
    assert original_packet.count(marker) == 1
    malformed = original_packet.replace(
        marker, f'"{field}":'.encode("ascii") + exponent,
    )
    with pytest.raises(packet_review.DetachedV3PacketRejected):
        packet_review.review_detached_v3_packet(malformed)


@pytest.mark.parametrize("notation", (b"1e-9999", b"1.0e+0", b"1E0"))
def test_numeric_alternate_spelling_cannot_pass_canonical_byte_gate(
    notation: bytes,
) -> None:
    original = _packet()
    assert original.count(b'"capacity_gib":12.0') == 1
    changed = original.replace(b'"capacity_gib":12.0', b'"capacity_gib":' + notation)
    with pytest.raises(packet_review.DetachedV3PacketRejected):
        packet_review.review_detached_v3_packet(changed)


def test_valid_packet_still_has_no_dispatch_or_spend_authority() -> None:
    result = packet_review.review_detached_v3_packet(_packet())
    assert len(result.packet_sha256) == 64
    assert result.paid_compute_authorized is False
    assert result.training_authorized is False
    assert result.candidate_promotion_authorized is False
    assert result.provenance_authenticated is False
