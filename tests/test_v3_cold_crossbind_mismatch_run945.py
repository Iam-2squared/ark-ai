"""Canonical but contradictory synthetic V3 packets fail closed after restart.

No GPU, external compute, model, protected evaluation, cost authorization,
Candidate generation, or promotion is performed or implied.
"""

from __future__ import annotations

import json
import subprocess
import sys

import pytest

from ark.v3_detached_packet_review import (
    DetachedV3PacketRejected,
    review_detached_v3_packet,
)

_CHILD = """
import sys
from ark.v3_detached_packet_review import (
    DetachedV3PacketRejected, review_detached_v3_packet,
)
try:
    result = review_detached_v3_packet(sys.stdin.buffer.read())
except DetachedV3PacketRejected:
    print("DENIED")
else:
    assert result.training_authorized is False
    assert result.paid_compute_authorized is False
    assert result.candidate_promotion_authorized is False
    assert result.provenance_authenticated is False
    print("REVIEWED")
"""


def _packet(change: str) -> bytes:
    probe = "a" * 64
    snapshot = {
        "device": "cuda:0", "capacity_gib": 12.0,
        "tokenizer_probe_sha256": probe,
        "wall_clock_timeout_minutes": 20,
    }
    evidence = {
        "device": "cuda:0", "reported_capacity_gib": 12.0,
        "tokenizer_probe_sha256": probe,
        "peak_vram_mib": 4096.0, "peak_reserved_vram_mib": 6144.0,
        "wall_seconds": 300.0,
    }
    if change == "device":
        evidence["device"] = "cuda:1"
    elif change == "capacity":
        evidence["reported_capacity_gib"] = 13.0
    elif change == "tokenizer":
        evidence["tokenizer_probe_sha256"] = "b" * 64
    elif change == "vram-order":
        evidence["peak_vram_mib"] = 7000.0
        evidence["peak_reserved_vram_mib"] = 6000.0
    elif change == "vram-capacity":
        evidence["peak_reserved_vram_mib"] = 13000.0
    elif change == "timeout":
        evidence["wall_seconds"] = 1201.0
    elif change == "integer-precision":
        snapshot["capacity_gib"] = 2**53 + 1
        evidence["reported_capacity_gib"] = 2**53 + 1
    else:
        raise AssertionError("unexpected synthetic mismatch")
    return json.dumps(
        {"snapshot": snapshot, "evidence": evidence},
        sort_keys=True, ensure_ascii=True, separators=(",", ":"), allow_nan=False,
    ).encode("ascii")


@pytest.mark.parametrize(
    "change",
    (
        "device", "capacity", "tokenizer", "vram-order",
        "vram-capacity", "timeout", "integer-precision",
    ),
)
def test_canonical_crossbind_mismatch_fails_closed_in_cold_interpreter(
    change: str,
) -> None:
    packet = _packet(change)
    assert json.dumps(
        json.loads(packet), sort_keys=True, ensure_ascii=True,
        separators=(",", ":"), allow_nan=False,
    ).encode("ascii") == packet
    assert len(packet) <= 4096
    with pytest.raises(DetachedV3PacketRejected):
        review_detached_v3_packet(packet)
    child = subprocess.run(
        [sys.executable, "-c", _CHILD], input=packet,
        check=True, capture_output=True, timeout=20,
    )
    assert child.stderr == b""
    assert child.stdout.strip() == b"DENIED"
