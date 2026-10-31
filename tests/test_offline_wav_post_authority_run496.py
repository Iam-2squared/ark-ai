"""WAV metadata inventory must reject mutations by late false authority getters."""

from __future__ import annotations

import hashlib
import struct

import pytest

import ark.offline_pcm_wav as wave


def _request():
    samples = b"\x01\x00" * 80
    fmt = struct.pack("<HHIIHH", 1, 1, 8_000, 16_000, 2, 16)
    body = (
        b"WAVE" + b"fmt " + struct.pack("<I", 16) + fmt
        + b"data" + struct.pack("<I", len(samples)) + samples
    )
    data = b"RIFF" + struct.pack("<I", len(body)) + body
    return wave.OfflineWaveRequest(
        "a" * 64, "b" * 64, hashlib.sha256(data).hexdigest(), data,
    )


@pytest.mark.parametrize(
    ("field", "forged"),
    (
        ("pcm_sha256", "f" * 64),
        ("frame_count", 9_999),
        ("duration_ms_floor", 0),
        ("duration_ms_remainder", 99),
    ),
)
def test_last_false_authority_getter_cannot_rewrite_inventory(
    monkeypatch, field, forged,
):
    def mutate(result):
        object.__setattr__(result, field, forged)
        return False

    monkeypatch.setattr(
        wave._REVIEW_TYPE,
        "authorized_to_disclose",
        property(mutate),
    )
    with pytest.raises(wave.OfflineWaveRejected, match="after authority"):
        wave.inspect_local_pcm_wav(_request())


def test_stable_pcm_fixture_remains_metadata_only():
    review = wave.inspect_local_pcm_wav(_request())
    assert review.channel_count == 1
    assert review.frame_count == 80
    assert review.duration_ms_floor == 10
    assert review.authorized_to_disclose is False
    assert review.microphone_provenance_verified is False
