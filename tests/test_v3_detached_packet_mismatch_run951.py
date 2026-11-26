"""Run951: disconnected V3 packet mismatch review remains free-only.

No actual hardware, model weights, Candidate training, approval, provider,
filesystem, protected evaluation, external compute, or paid service is used.
"""

from __future__ import annotations

import hashlib
import json

import pytest

from ark.v3_detached_packet_review import (
    DetachedV3PacketRejected,
    review_detached_v3_packet,
)


def _packet() -> dict[str, dict[str, object]]:
    return {
        "snapshot": {
            "device": "synthetic-local-gpu",
            "capacity_gib": 8.0,
            "tokenizer_probe_sha256": "a" * 64,
            "wall_clock_timeout_minutes": 60,
        },
        "evidence": {
            "device": "synthetic-local-gpu",
            "reported_capacity_gib": 8.0,
            "tokenizer_probe_sha256": "a" * 64,
            "peak_vram_mib": 1_024.0,
            "peak_reserved_vram_mib": 2_048.0,
            "wall_seconds": 30.0,
        },
    }


def _encoded(data: object) -> bytes:
    return json.dumps(
        data, ensure_ascii=True, sort_keys=True, separators=(",", ":"),
        allow_nan=False,
    ).encode("ascii")


@pytest.mark.parametrize(("section", "field", "value"), (
    ("evidence", "device", "synthetic-other-device"),
    ("evidence", "reported_capacity_gib", 9.0),
    ("evidence", "tokenizer_probe_sha256", "b" * 64),
    ("evidence", "peak_reserved_vram_mib", 900.0),
    ("evidence", "wall_seconds", 3_601.0),
    ("snapshot", "wall_clock_timeout_minutes", True),
    ("snapshot", "capacity_gib", 9_007_199_254_740_993),
))
def test_canonical_but_contradictory_v3_evidence_never_grants_authority(
    section: str, field: str, value: object,
) -> None:
    packet = _packet()
    packet[section][field] = value
    with pytest.raises(DetachedV3PacketRejected):
        review_detached_v3_packet(_encoded(packet))


def test_valid_synthetic_v3_packet_is_only_digest_review() -> None:
    payload = _encoded(_packet())
    review = review_detached_v3_packet(payload)
    assert review.packet_sha256 == hashlib.sha256(payload).hexdigest()
    assert len(review.crossbind_digest) == 64
    assert review.checks == (
        "device", "capacity", "tokenizer_probe", "peak_vram_order",
        "wall_clock_budget",
    )
    assert review.paid_compute_authorized is False
    assert review.training_authorized is False
    assert review.candidate_promotion_authorized is False
    assert review.provenance_authenticated is False


@pytest.mark.parametrize("variation", (
    b"\x20",
    b"\x0a",
))
def test_noncanonical_v3_packet_bytes_are_rejected(variation: bytes) -> None:
    payload = _encoded(_packet())
    with pytest.raises(DetachedV3PacketRejected):
        review_detached_v3_packet(variation + payload)
