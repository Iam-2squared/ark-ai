"""Free-only V3 packet grammar and crossbind regressions (never execute training)."""

from __future__ import annotations

import json

import pytest

from ark import v3_detached_packet_review as packet_review


def _components():
    probe = "a" * 64
    snapshot = {
        "device": "cuda:0",
        "capacity_gib": 12.0,
        "tokenizer_probe_sha256": probe,
        "wall_clock_timeout_minutes": 20,
    }
    evidence = {
        "device": "cuda:0",
        "reported_capacity_gib": 12.0,
        "tokenizer_probe_sha256": probe,
        "peak_vram_mib": 4096.0,
        "peak_reserved_vram_mib": 6144.0,
        "wall_seconds": 300.0,
    }
    return snapshot, evidence


def _canonical(snapshot, evidence):
    return json.dumps(
        {"snapshot": snapshot, "evidence": evidence},
        ensure_ascii=True, sort_keys=True,
        separators=(",", ":"), allow_nan=False,
    ).encode("ascii")


def test_valid_synthetic_packet_is_cryptographically_bound_but_never_approved():
    snapshot, evidence = _components()
    encoded = _canonical(snapshot, evidence)
    receipt = packet_review.review_detached_v3_packet(encoded)
    assert receipt == packet_review.review_detached_v3_packet(encoded)
    assert len(receipt.packet_sha256) == 64
    assert len(receipt.crossbind_digest) == 64
    assert receipt.paid_compute_authorized is False
    assert receipt.training_authorized is False
    assert receipt.candidate_promotion_authorized is False
    assert receipt.provenance_authenticated is False
    assert receipt.checks == (
        "device", "capacity", "tokenizer_probe",
        "peak_vram_order", "wall_clock_budget",
    )


@pytest.mark.parametrize(
    "invalid",
    (
        "extra-root", "missing-root", "extra-snapshot", "missing-evidence",
        "device-mismatch", "probe-mismatch", "capacity-mismatch",
        "bool-capacity", "lossy-capacity", "negative-vram",
        "peak-over-reservation", "reserved-over-capacity",
        "wall-exceeded", "zero-timeout", "unicode-device",
    ),
)
def test_untrusted_packet_fails_exact_free_only_crossbinding(invalid):
    snapshot, evidence = _components()
    data = {"snapshot": snapshot, "evidence": evidence}
    if invalid == "extra-root":
        data["authorized"] = True
    elif invalid == "missing-root":
        del data["evidence"]
    elif invalid == "extra-snapshot":
        snapshot["paid_compute_authorized"] = True
    elif invalid == "missing-evidence":
        del evidence["wall_seconds"]
    elif invalid == "device-mismatch":
        evidence["device"] = "cuda:1"
    elif invalid == "probe-mismatch":
        evidence["tokenizer_probe_sha256"] = "b" * 64
    elif invalid == "capacity-mismatch":
        evidence["reported_capacity_gib"] = 16.0
    elif invalid == "bool-capacity":
        snapshot["capacity_gib"] = True
    elif invalid == "lossy-capacity":
        snapshot["capacity_gib"] = 2**53 + 1
        evidence["reported_capacity_gib"] = float(2**53 + 1)
    elif invalid == "negative-vram":
        evidence["peak_vram_mib"] = -1.0
    elif invalid == "peak-over-reservation":
        evidence["peak_vram_mib"] = 7000.0
    elif invalid == "reserved-over-capacity":
        evidence["peak_reserved_vram_mib"] = 13000.0
    elif invalid == "wall-exceeded":
        evidence["wall_seconds"] = 1201.0
    elif invalid == "zero-timeout":
        snapshot["wall_clock_timeout_minutes"] = 0
    else:
        snapshot["device"] = "cuda:零"
        evidence["device"] = "cuda:零"
    encoded = json.dumps(
        data, ensure_ascii=True, sort_keys=True,
        separators=(",", ":"), allow_nan=False,
    ).encode("ascii")
    with pytest.raises(packet_review.DetachedV3PacketRejected):
        packet_review.review_detached_v3_packet(encoded)


@pytest.mark.parametrize(
    "invalid",
    (
        "bytes-prefix", "whitespace", "duplicate-root",
        "duplicate-nested", "nan", "overflow", "invalid-utf8", "oversize",
    ),
)
def test_noncanonical_or_ambiguous_exact_packet_bytes_rejected(invalid):
    snapshot, evidence = _components()
    encoded = _canonical(snapshot, evidence)
    if invalid == "bytes-prefix":
        encoded = b"\xef\xbb\xbf" + encoded
    elif invalid == "whitespace":
        encoded = encoded.replace(b":", b": ", 1)
    elif invalid == "duplicate-root":
        encoded = (
            b'{"evidence":' + json.dumps(
                evidence, sort_keys=True, separators=(",", ":"),
            ).encode("ascii")
            + b',"snapshot":' + json.dumps(
                snapshot, sort_keys=True, separators=(",", ":"),
            ).encode("ascii")
            + b',"snapshot":{}}'
        )
    elif invalid == "duplicate-nested":
        encoded = encoded.replace(
            b'{"capacity_gib":', b'{"capacity_gib":12.0,"capacity_gib":', 1,
        )
    elif invalid == "nan":
        encoded = encoded.replace(b"300.0", b"NaN")
    elif invalid == "overflow":
        encoded = encoded.replace(b"300.0", b"1e309")
    elif invalid == "invalid-utf8":
        encoded += b"\xff"
    else:
        encoded += b" " * (4097 - len(encoded))
    with pytest.raises(packet_review.DetachedV3PacketRejected):
        packet_review.review_detached_v3_packet(encoded)


@pytest.mark.parametrize("value", (bytearray(b"{}"), memoryview(b"{}"), "{}", None))
def test_only_exact_immutable_packet_bytes_accepted(value):
    with pytest.raises(packet_review.DetachedV3PacketRejected):
        packet_review.review_detached_v3_packet(value)


@pytest.mark.parametrize("field", ("training_authorized", "paid_compute_authorized"))
def test_rebound_denial_getters_refused_before_parsing(monkeypatch, field):
    snapshot, evidence = _components()
    touched = []

    def injected(_self):
        touched.append("executed")
        return False

    with monkeypatch.context() as patch:
        patch.setattr(
            packet_review.DetachedV3PacketReview,
            field, property(injected),
        )
        with pytest.raises(
            packet_review.DetachedV3PacketRejected, match="protocol changed",
        ):
            packet_review.review_detached_v3_packet(
                _canonical(snapshot, evidence),
            )
    assert touched == []
