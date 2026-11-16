"""Free-only V3 packet bytes and normalized cross-binding retain separate identities.

Only in-memory synthetic JSON is parsed; no GPU, Candidate, protected evaluation
or training service is touched.
"""

from __future__ import annotations

import hashlib
import json

import pytest

from ark.v3_detached_packet_review import review_detached_v3_packet


def _vectors():
    probe = "a" * 64
    return (
        {
            "device": "cuda:0",
            "capacity_gib": 12.0,
            "tokenizer_probe_sha256": probe,
            "wall_clock_timeout_minutes": 20,
        },
        {
            "device": "cuda:0",
            "reported_capacity_gib": 12.0,
            "tokenizer_probe_sha256": probe,
            "peak_vram_mib": 4096.0,
            "peak_reserved_vram_mib": 6144.0,
            "wall_seconds": 300.0,
        },
    )


def _packet(snapshot, evidence):
    return json.dumps(
        {"snapshot": snapshot, "evidence": evidence},
        sort_keys=True, ensure_ascii=True, separators=(",", ":"), allow_nan=False,
    ).encode("ascii")


@pytest.mark.parametrize(
    "field,new_value",
    (
        ("device", "cuda:1"),
        ("capacity_gib", 13.0),
        ("tokenizer_probe_sha256", "b" * 64),
        ("wall_clock_timeout_minutes", 21),
        ("peak_vram_mib", 4097.0),
        ("peak_reserved_vram_mib", 6145.0),
        ("wall_seconds", 301.0),
    ),
)
def test_each_independent_valid_evidence_change_rebinds_both_digests(
    field: str, new_value: object,
):
    snapshot, evidence = _vectors()
    original = review_detached_v3_packet(_packet(snapshot, evidence))
    if field == "device":
        snapshot[field] = new_value
        evidence[field] = new_value
    elif field == "capacity_gib":
        snapshot[field] = new_value
        evidence["reported_capacity_gib"] = new_value
    elif field == "tokenizer_probe_sha256":
        snapshot[field] = new_value
        evidence[field] = new_value
    elif field == "wall_clock_timeout_minutes":
        snapshot[field] = new_value
    else:
        evidence[field] = new_value
    encoded = _packet(snapshot, evidence)
    current = review_detached_v3_packet(encoded)
    assert current.packet_sha256 == hashlib.sha256(encoded).hexdigest()
    assert current.packet_sha256 != original.packet_sha256
    assert current.crossbind_digest != original.crossbind_digest
    assert current.paid_compute_authorized is False
    assert current.training_authorized is False
    assert current.candidate_promotion_authorized is False
    assert current.provenance_authenticated is False


def test_semantically_equal_numeric_formats_keep_packet_custody_separate():
    snapshot, evidence = _vectors()
    original = review_detached_v3_packet(_packet(snapshot, evidence))
    snapshot["capacity_gib"] = 12
    evidence["reported_capacity_gib"] = 12
    changed = _packet(snapshot, evidence)
    reviewed = review_detached_v3_packet(changed)
    # Cross-binding normalizes exact positive integers into floats. This is
    # not authority to ignore the exact user-supplied byte-level evidence.
    assert reviewed.crossbind_digest == original.crossbind_digest
    assert reviewed.packet_sha256 != original.packet_sha256
    assert reviewed.packet_sha256 == hashlib.sha256(changed).hexdigest()
    assert reviewed.training_authorized is False
    assert reviewed.provenance_authenticated is False
