"""No executable equality during detached free-only V3 protocol refusal."""

from __future__ import annotations

import json

import pytest

from ark import v3_detached_packet_review as mod


def _packet() -> bytes:
    probe = "a" * 64
    data = {
        "snapshot": {
            "device": "cuda:0",
            "capacity_gib": 12.0,
            "tokenizer_probe_sha256": probe,
            "wall_clock_timeout_minutes": 20,
        },
        "evidence": {
            "device": "cuda:0",
            "reported_capacity_gib": 12.0,
            "tokenizer_probe_sha256": probe,
            "peak_vram_mib": 4096.0,
            "peak_reserved_vram_mib": 6144.0,
            "wall_seconds": 300.0,
        },
    }
    return json.dumps(
        data, ensure_ascii=True, sort_keys=True, separators=(",", ":"),
        allow_nan=False,
    ).encode("ascii")


@pytest.mark.parametrize("index", (0, 1, 2))
def test_class_protocol_drift_denied_without_poison_equality(
    monkeypatch: pytest.MonkeyPatch, index: int,
) -> None:
    calls: list[str] = []

    class Poison:
        def __eq__(self, _other: object) -> bool:
            calls.append("eq")
            raise AssertionError("untrusted comparison executed")

        def __ne__(self, _other: object) -> bool:
            calls.append("ne")
            raise AssertionError("untrusted comparison executed")

    originals = list(mod._ORIGINAL_CLASSES)
    originals[index] = Poison()
    with monkeypatch.context() as patch:
        patch.setattr(mod, "_ORIGINAL_CLASSES", tuple(originals))
        with pytest.raises(mod.DetachedV3PacketRejected, match="protocol changed"):
            mod.review_detached_v3_packet(_packet())
    assert calls == []


def test_valid_offline_packet_still_refuses_all_authority() -> None:
    result = mod.review_detached_v3_packet(_packet())
    assert result.paid_compute_authorized is False
    assert result.training_authorized is False
    assert result.candidate_promotion_authorized is False
    assert result.provenance_authenticated is False
