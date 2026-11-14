"""Adversarial free-only V3 packet boundary tests; never start real compute.

The packet is an invented detached fixture. Passing it does not authenticate
provenance, approve external cost, evaluate a model, or promote a Candidate.
"""

from __future__ import annotations

import json

import pytest

from ark import v3_detached_packet_review as packet_module
from ark import v3_detached_preflight_crossbind as crossbind
from ark.v3_detached_packet_review import (
    DetachedV3PacketRejected,
    DetachedV3PacketReview,
    review_detached_v3_packet,
)


def _fixture(*, seconds: float = 60.0, reserved: float = 8192.0) -> bytes:
    document = {
        "snapshot": {
            "device": "cuda:0",
            "capacity_gib": 8.0,
            "tokenizer_probe_sha256": "f" * 64,
            "wall_clock_timeout_minutes": 1,
        },
        "evidence": {
            "device": "cuda:0",
            "reported_capacity_gib": 8.0,
            "tokenizer_probe_sha256": "f" * 64,
            "peak_vram_mib": 256.0,
            "peak_reserved_vram_mib": reserved,
            "wall_seconds": seconds,
        },
    }
    return json.dumps(
        document, ensure_ascii=True, sort_keys=True,
        separators=(",", ":"), allow_nan=False,
    ).encode("ascii")


def test_exact_vram_and_wall_clock_boundaries_remain_non_authorizing() -> None:
    result = review_detached_v3_packet(_fixture())
    assert type(result) is DetachedV3PacketReview
    assert result.checks == (
        "device", "capacity", "tokenizer_probe", "peak_vram_order",
        "wall_clock_budget",
    )
    for denial in (
        "paid_compute_authorized", "training_authorized",
        "candidate_promotion_authorized", "provenance_authenticated",
    ):
        assert getattr(result, denial) is False


@pytest.mark.parametrize(
    ("needle", "replacement"),
    (
        (b'"wall_seconds":60.0', b'"wall_seconds":1e999'),
        (b'"wall_seconds":60.0', b'"wall_seconds":0.0'),
        (b'"wall_seconds":60.0', b'"wall_seconds":-0.0'),
        (b'"wall_seconds":60.0', b'"wall_seconds":60.00000001'),
        (b'"peak_reserved_vram_mib":8192.0',
         b'"peak_reserved_vram_mib":8192.00001'),
        (b'"peak_reserved_vram_mib":8192.0',
         b'"peak_reserved_vram_mib":255.9999'),
    ),
)
def test_strict_boundary_mutations_refuse_computation_authority(
    needle: bytes, replacement: bytes,
) -> None:
    original = _fixture()
    assert needle in original
    with pytest.raises(DetachedV3PacketRejected):
        review_detached_v3_packet(original.replace(needle, replacement))


@pytest.mark.parametrize("prefix", (b"\xef\xbb\xbf", b"\xff", b"\x00"))
def test_noncanonical_prefix_or_invalid_utf8_denied(prefix: bytes) -> None:
    with pytest.raises(DetachedV3PacketRejected):
        review_detached_v3_packet(prefix + _fixture())


@pytest.mark.parametrize(
    "attribute",
    (
        "paid_compute_authorized", "training_authorized",
        "candidate_promotion_authorized", "provenance_authenticated",
    ),
)
def test_mutated_packet_receipt_authority_descriptor_is_denied_preaccess(
    monkeypatch, attribute: str,
) -> None:
    def forbidden(_self):
        raise AssertionError("injected permission property was evaluated")

    monkeypatch.setattr(
        DetachedV3PacketReview, attribute, property(forbidden),
    )
    with pytest.raises(DetachedV3PacketRejected, match="protocol changed"):
        review_detached_v3_packet(_fixture())


def test_changed_crossbinding_callback_is_denied_before_call(monkeypatch) -> None:
    def forbidden(*_args, **_kwargs):
        raise AssertionError("unreviewed crossbind callback invoked")

    monkeypatch.setattr(crossbind, "review_detached_v3_preflight", forbidden)
    with pytest.raises(DetachedV3PacketRejected, match="protocol changed"):
        packet_module.review_detached_v3_packet(_fixture())
