"""Run966: packet result-vector truncation never grants V3 authorization."""

from __future__ import annotations

import json

import pytest

from ark import v3_detached_packet_review as packet_review


def _packet() -> bytes:
    data = {
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
            "wall_seconds": 300.0,
        },
    }
    return json.dumps(
        data, sort_keys=True, separators=(",", ":"), ensure_ascii=True,
    ).encode("ascii")


@pytest.mark.parametrize("name", (
    "_REPORT_FIELDS",
    "_DENIALS",
    "_HOOKS",
))
def test_truncated_result_guards_rejected_before_deserialization(
    monkeypatch, name: str,
) -> None:
    with monkeypatch.context() as patch:
        patch.setattr(packet_review, name, ())
        with pytest.raises(
            packet_review.DetachedV3PacketRejected, match="protocol changed",
        ):
            packet_review.review_detached_v3_packet(_packet())


def test_valid_offline_packet_still_has_no_cost_or_candidate_authority() -> None:
    result = packet_review.review_detached_v3_packet(_packet())
    assert result.paid_compute_authorized is False
    assert result.training_authorized is False
    assert result.candidate_promotion_authorized is False
    assert result.provenance_authenticated is False
