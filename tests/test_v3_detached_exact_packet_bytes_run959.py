"""Run959: strict detached V3 packet-byte identity, with zero authority.

The packet is a synthetic local fixture. No GPU, paid runtime, Candidate,
user approval, protected evaluation, or real model input is requested.
"""

from __future__ import annotations

import hashlib
import json

import pytest

from ark.v3_detached_packet_review import (
    DetachedV3PacketRejected,
    review_detached_v3_packet,
)


def _fixture() -> dict[str, dict[str, object]]:
    return {
        "snapshot": {
            "device": "fixture-gpu",
            "capacity_gib": 8.0,
            "tokenizer_probe_sha256": "a" * 64,
            "wall_clock_timeout_minutes": 10,
        },
        "evidence": {
            "device": "fixture-gpu",
            "reported_capacity_gib": 8.0,
            "tokenizer_probe_sha256": "a" * 64,
            "peak_vram_mib": 1024.0,
            "peak_reserved_vram_mib": 2048.0,
            "wall_seconds": 15.0,
        },
    }


def _encode(data: object) -> bytes:
    return json.dumps(
        data, sort_keys=True, separators=(",", ":"), ensure_ascii=True,
        allow_nan=False,
    ).encode("ascii")


@pytest.mark.parametrize("attack", (
    "duplicate-nested-key",
    "noncanonical-device-escape",
    "number-overflow",
    "nan-token",
    "utf8-bom",
    "invalid-utf8",
    "oversize",
    "trailing-nul",
))
def test_detached_packet_rejects_ambiguous_or_unbounded_byte_forms(
    attack: str,
) -> None:
    canonical = _encode(_fixture())
    assert len(canonical) < 4096
    if attack == "duplicate-nested-key":
        malformed = canonical.replace(
            b'"device":"fixture-gpu"',
            b'"device":"fixture-gpu","device":"fixture-gpu"', 1,
        )
    elif attack == "noncanonical-device-escape":
        malformed = canonical.replace(
            b'"device":"fixture-gpu"',
            b'"device":"fixture\\u002dgpu"', 1,
        )
    elif attack == "number-overflow":
        malformed = canonical.replace(
            b'"wall_seconds":15.0', b'"wall_seconds":1e309', 1,
        )
    elif attack == "nan-token":
        malformed = canonical.replace(
            b'"wall_seconds":15.0', b'"wall_seconds":NaN', 1,
        )
    elif attack == "utf8-bom":
        malformed = b"\xef\xbb\xbf" + canonical
    elif attack == "invalid-utf8":
        malformed = canonical + b"\xff"
    elif attack == "oversize":
        malformed = canonical + b" " * 4096
    else:
        malformed = canonical + b"\x00"
    assert malformed != canonical
    with pytest.raises(DetachedV3PacketRejected):
        review_detached_v3_packet(malformed)


def test_distinct_canonical_numeric_forms_have_distinct_packet_hashes(
) -> None:
    first = _fixture()
    second = _fixture()
    second["snapshot"]["capacity_gib"] = 8
    second["evidence"]["reported_capacity_gib"] = 8
    first_bytes = _encode(first)
    second_bytes = _encode(second)
    assert first_bytes != second_bytes

    first_review = review_detached_v3_packet(first_bytes)
    second_review = review_detached_v3_packet(second_bytes)
    assert first_review.packet_sha256 == hashlib.sha256(first_bytes).hexdigest()
    assert second_review.packet_sha256 == hashlib.sha256(second_bytes).hexdigest()
    assert first_review.packet_sha256 != second_review.packet_sha256
    # Both cross-check the same numerical evidence; neither is authenticated.
    assert first_review.crossbind_digest == second_review.crossbind_digest
    for report in (first_review, second_review):
        assert report.paid_compute_authorized is False
        assert report.training_authorized is False
        assert report.candidate_promotion_authorized is False
        assert report.provenance_authenticated is False
