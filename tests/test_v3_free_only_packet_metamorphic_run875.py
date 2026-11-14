"""Free-only adversarial V3 packet mutations; no runtime, approval, or GPU access.

The fixture is synthetic JSON and has no signed provenance.  A passing local
crossbind review must never authorize paid compute or Candidate promotion.
"""

from __future__ import annotations

import copy
import json

import pytest

from ark.v3_detached_packet_review import (
    DetachedV3PacketRejected,
    review_detached_v3_packet,
)


def _packet() -> dict:
    return {
        "snapshot": {
            "device": "cuda:0",
            "capacity_gib": 8.0,
            "tokenizer_probe_sha256": "a" * 64,
            "wall_clock_timeout_minutes": 1,
        },
        "evidence": {
            "device": "cuda:0",
            "reported_capacity_gib": 8.0,
            "tokenizer_probe_sha256": "a" * 64,
            "peak_vram_mib": 512.0,
            "peak_reserved_vram_mib": 768.0,
            "wall_seconds": 5.0,
        },
    }


def _encode(packet: dict) -> bytes:
    return json.dumps(
        packet, ensure_ascii=True, sort_keys=True,
        separators=(",", ":"), allow_nan=False,
    ).encode("ascii")


def test_synthetic_v3_packet_receipt_never_grants_authority() -> None:
    result = review_detached_v3_packet(_encode(_packet()))
    assert len(result.packet_sha256) == 64
    assert len(result.crossbind_digest) == 64
    assert result.provenance_authenticated is False
    assert result.paid_compute_authorized is False
    assert result.training_authorized is False
    assert result.candidate_promotion_authorized is False


@pytest.mark.parametrize(
    ("section", "field", "replacement"),
    [
        ("evidence", "device", "cuda:1"),
        ("evidence", "tokenizer_probe_sha256", "b" * 64),
        ("evidence", "reported_capacity_gib", 7.0),
        ("evidence", "peak_vram_mib", 769.0),
        ("evidence", "peak_reserved_vram_mib", 8193.0),
        ("evidence", "wall_seconds", 60.001),
        ("snapshot", "wall_clock_timeout_minutes", True),
        ("snapshot", "capacity_gib", 2**200),
        ("snapshot", "device", "cuda:0\u2026"),
    ],
)
def test_synthetic_v3_mutations_fail_closed(
    section: str, field: str, replacement: object,
) -> None:
    packet = copy.deepcopy(_packet())
    packet[section][field] = replacement
    with pytest.raises(DetachedV3PacketRejected):
        review_detached_v3_packet(_encode(packet))


@pytest.mark.parametrize("malformation", ("trailing", "extra", "duplicate"))
def test_synthetic_v3_json_framing_rejects_ambiguous_bytes(
    malformation: str,
) -> None:
    packet = _packet()
    if malformation == "trailing":
        encoded = _encode(packet) + b"\n"
    elif malformation == "extra":
        packet["candidate_approved"] = True
        encoded = _encode(packet)
    else:
        encoded = _encode(packet).replace(
            b'"device":"cuda:0",',
            b'"device":"cuda:0","device":"cuda:0",',
            1,
        )
        assert encoded != _encode(packet)
    with pytest.raises(DetachedV3PacketRejected):
        review_detached_v3_packet(encoded)
