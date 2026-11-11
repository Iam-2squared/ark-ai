"""V3 JSON evidence packet validation is strict, inert, and byte-bound."""

from __future__ import annotations

import hashlib
import json

import pytest

from ark import v3_detached_packet_review as mod

_SHA = "a" * 64


def _payload():
    return {
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
    }


def _encode(payload):
    return json.dumps(
        payload, ensure_ascii=True, sort_keys=True,
        separators=(",", ":"), allow_nan=False,
    ).encode("ascii")


def test_canonical_packet_hash_covers_exact_supplied_bytes_not_approval():
    packet = _encode(_payload())
    receipt = mod.review_detached_v3_packet(packet)
    assert receipt == mod.review_detached_v3_packet(packet)
    assert receipt.packet_sha256 == hashlib.sha256(packet).hexdigest()
    assert len(receipt.crossbind_digest) == 64
    assert receipt.checks == (
        "device", "capacity", "tokenizer_probe", "peak_vram_order",
        "wall_clock_budget",
    )
    assert receipt.paid_compute_authorized is False
    assert receipt.training_authorized is False
    assert receipt.candidate_promotion_authorized is False
    assert receipt.provenance_authenticated is False


@pytest.mark.parametrize("packet", (
    "", True, None, bytearray(b"{}"), b"", b"x" * 4097,
))
def test_nonexact_or_oversized_carrier_rejected_before_json(packet):
    with pytest.raises(mod.DetachedV3PacketRejected, match="packet bytes"):
        mod.review_detached_v3_packet(packet)


@pytest.mark.parametrize("packet", (
    b"[]",
    b"null",
    b"{}",
    b'{"evidence":{},"evidence":{},"snapshot":{}}',
    b'{"evidence":NaN,"snapshot":{}}',
    b'{"evidence":Infinity,"snapshot":{}}',
    b"\xff",
    b"\xef\xbb\xbf{}",
    b'{"evidence":{},"snapshot":{}}\n',
    b'{"snapshot":{},"evidence":{}}',
))
def test_invalid_duplicate_nonfinite_or_noncanonical_packet_rejected(packet):
    with pytest.raises(mod.DetachedV3PacketRejected):
        mod.review_detached_v3_packet(packet)


@pytest.mark.parametrize(("section", "field", "value"), (
    ("snapshot", "device", "cuda:1"),
    ("snapshot", "capacity_gib", True),
    ("snapshot", "capacity_gib", 2**53 + 1),
    ("snapshot", "wall_clock_timeout_minutes", 0),
    ("evidence", "tokenizer_probe_sha256", "b" * 64),
    ("evidence", "peak_vram_mib", 8192.0),
    ("evidence", "peak_reserved_vram_mib", 13000.0),
    ("evidence", "wall_seconds", 1201.0),
))
def test_crossbinding_and_resource_bounds_stay_fail_closed(
    section, field, value,
):
    payload = _payload()
    payload[section][field] = value
    with pytest.raises(mod.DetachedV3PacketRejected):
        mod.review_detached_v3_packet(_encode(payload))


@pytest.mark.parametrize(("section", "kind"), (
    ("snapshot", "missing"),
    ("snapshot", "extra"),
    ("evidence", "missing"),
    ("evidence", "extra"),
))
def test_exact_section_keys_required(section, kind):
    payload = _payload()
    if kind == "missing":
        payload[section].pop(next(iter(payload[section])))
    else:
        payload[section]["unreviewed_field"] = "untrusted"
    with pytest.raises(
        mod.DetachedV3PacketRejected, match="unexpected or missing",
    ):
        mod.review_detached_v3_packet(_encode(payload))


def test_valid_but_different_bytes_are_not_one_packet():
    payload = _payload()
    original = _encode(payload)
    payload["evidence"]["wall_seconds"] = 301.0
    changed = _encode(payload)
    first = mod.review_detached_v3_packet(original)
    second = mod.review_detached_v3_packet(changed)
    assert first.packet_sha256 != second.packet_sha256
    assert first.crossbind_digest != second.crossbind_digest
    assert second.training_authorized is False


@pytest.mark.parametrize("name", (
    "paid_compute_authorized",
    "training_authorized",
    "candidate_promotion_authorized",
    "provenance_authenticated",
))
def test_denial_getter_substitution_never_executed(monkeypatch, name):
    called = []

    def injected(_self):
        called.append(name)
        return False

    with monkeypatch.context() as patch:
        patch.setattr(mod.DetachedV3PacketReview, name, property(injected))
        with pytest.raises(
            mod.DetachedV3PacketRejected, match="protocol changed",
        ):
            mod.review_detached_v3_packet(_encode(_payload()))
    assert called == []


def test_crossbind_dependency_substitution_never_called(monkeypatch):
    called = []

    def injected(*args):
        called.append(args)
        raise RuntimeError("must not be invoked")

    with monkeypatch.context() as patch:
        patch.setattr(mod.crossbind, "review_detached_v3_preflight", injected)
        with pytest.raises(
            mod.DetachedV3PacketRejected, match="protocol changed",
        ):
            mod.review_detached_v3_packet(_encode(_payload()))
    assert called == []
