"""Offline V3 review must retain exact packet custody in cold interpreters.

Synthetic JSON only: no GPU, model, external service, approval or promotion.
"""

from __future__ import annotations

import hashlib
import json
import subprocess
import sys

import pytest

from ark.v3_detached_packet_review import (
    DetachedV3PacketRejected,
    review_detached_v3_packet,
)

_CHILD = """
import json
import sys

from ark.v3_detached_packet_review import (
    DetachedV3PacketRejected,
    review_detached_v3_packet,
)

try:
    review = review_detached_v3_packet(sys.stdin.buffer.read())
except DetachedV3PacketRejected:
    print(json.dumps({"status": "DENIED"}))
else:
    print(json.dumps({
        "status": "REVIEWED",
        "packet_sha256": review.packet_sha256,
        "crossbind_digest": review.crossbind_digest,
        "checks": review.checks,
        "authority": [
            review.paid_compute_authorized, review.training_authorized,
            review.candidate_promotion_authorized, review.provenance_authenticated,
        ],
    }, sort_keys=True))
"""


def _packet(*, device: str = "cuda:0", wall_seconds: float = 300.0) -> bytes:
    probe = "a" * 64
    return json.dumps(
        {
            "snapshot": {
                "device": device, "capacity_gib": 12.0,
                "tokenizer_probe_sha256": probe,
                "wall_clock_timeout_minutes": 20,
            },
            "evidence": {
                "device": device, "reported_capacity_gib": 12.0,
                "tokenizer_probe_sha256": probe, "peak_vram_mib": 4096.0,
                "peak_reserved_vram_mib": 6144.0, "wall_seconds": wall_seconds,
            },
        },
        sort_keys=True, separators=(",", ":"), ensure_ascii=True, allow_nan=False,
    ).encode("ascii")


def _cold(packet: bytes) -> dict[str, object]:
    result = subprocess.run(
        [sys.executable, "-c", _CHILD], input=packet,
        capture_output=True, timeout=20, check=True,
    )
    assert result.stderr == b""
    return json.loads(result.stdout)


@pytest.mark.parametrize(
    ("device", "seconds"),
    (("cuda:0", 300.0), ("offline-fixture:1", 301.0), ("cuda:0", 302.0)),
)
def test_cold_exact_packet_and_crossbind_are_deterministic_and_inert(
    device: str, seconds: float,
) -> None:
    packet = _packet(device=device, wall_seconds=seconds)
    local = review_detached_v3_packet(packet)
    assert _cold(packet) == {
        "status": "REVIEWED",
        "packet_sha256": hashlib.sha256(packet).hexdigest(),
        "crossbind_digest": local.crossbind_digest,
        "checks": list(local.checks),
        "authority": [False, False, False, False],
    }
    assert local.training_authorized is False


@pytest.mark.parametrize(
    "invalid",
    (
        b'{"evidence":{},"evidence":{},"snapshot":{}}',
        _packet() + b"\\n",
        b"\\x00" + _packet(),
        b"x" * 4097,
    ),
)
def test_cold_invalid_packet_denies_without_leaking_payload(invalid: bytes) -> None:
    with pytest.raises(DetachedV3PacketRejected):
        review_detached_v3_packet(invalid)
    response = _cold(invalid)
    assert response == {"status": "DENIED"}
    assert b"cuda:0" not in json.dumps(response).encode("utf-8")
