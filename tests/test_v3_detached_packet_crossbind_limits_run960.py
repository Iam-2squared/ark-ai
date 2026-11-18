"""Run960: synthetic V3 JSON packet checks refuse numerical authority drift.

All evidence is anonymous in-memory JSON, with no GPU enumeration, model
weights, Candidate adapter, paid compute, or protected evaluation opened.
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


def _canonical(value: object) -> bytes:
    return json.dumps(
        value, sort_keys=True, ensure_ascii=True, separators=(",", ":"),
        allow_nan=False,
    ).encode("ascii")


@pytest.mark.parametrize(("section", "field", "invalid"), (
    ("snapshot", "device", "fixture gpu"),
    ("evidence", "device", "different-device"),
    ("snapshot", "capacity_gib", 0),
    ("snapshot", "capacity_gib", True),
    ("evidence", "reported_capacity_gib", 7.99),
    ("snapshot", "tokenizer_probe_sha256", "b" * 64),
    ("evidence", "tokenizer_probe_sha256", "c" * 64),
    ("evidence", "peak_vram_mib", 0),
    ("evidence", "peak_vram_mib", True),
    ("evidence", "peak_reserved_vram_mib", 1000.0),
    ("evidence", "peak_reserved_vram_mib", 9000.0),
    ("evidence", "wall_seconds", 601.0),
    ("evidence", "wall_seconds", "15"),
    ("snapshot", "wall_clock_timeout_minutes", True),
))
def test_detached_packet_rejects_false_or_inconsistent_resource_claims(
    section: str, field: str, invalid: object,
) -> None:
    packet = _packet()
    packet[section][field] = invalid
    raw = _canonical(packet)
    with pytest.raises(DetachedV3PacketRejected):
        review_detached_v3_packet(raw)


def test_exact_capacity_and_wall_time_boundaries_remain_deny_only() -> None:
    packet = _packet()
    packet["evidence"]["peak_vram_mib"] = 8192.0
    packet["evidence"]["peak_reserved_vram_mib"] = 8192.0
    packet["evidence"]["wall_seconds"] = 600.0
    raw = _canonical(packet)
    reviewed = review_detached_v3_packet(raw)
    assert reviewed.packet_sha256 == hashlib.sha256(raw).hexdigest()
    assert reviewed.checks == (
        "device", "capacity", "tokenizer_probe", "peak_vram_order",
        "wall_clock_budget",
    )
    assert reviewed.paid_compute_authorized is False
    assert reviewed.training_authorized is False
    assert reviewed.candidate_promotion_authorized is False
    assert reviewed.provenance_authenticated is False
